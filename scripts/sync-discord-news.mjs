import { writeFile } from "node:fs/promises";
import process from "node:process";
import { cleanDiscordText, convertDiscordAnnouncement } from "./discord-news-converter.mjs";

const token = process.env.DISCORD_BOT_TOKEN;
const channelIds = [...new Set(String(process.env.DISCORD_NEWS_CHANNEL_IDS || process.env.DISCORD_NEWS_CHANNEL_ID || "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean))];
const guildId = process.env.DISCORD_GUILD_ID;
const limit = Math.min(Math.max(Number(process.env.DISCORD_NEWS_LIMIT || 20), 1), 50);

function resolveDiscordMentions(value, message, roleNames, memberNames) {
  const userNames = new Map((message.mentions || []).map(mention => [
    mention.id,
    memberNames.get(mention.id) || mention.member?.nick || mention.global_name || mention.username
  ]));

  return String(value || "")
    .replace(/<@!?(\d+)>/g, (_match, id) => `@${userNames.get(id) || "사용자"}`)
    .replace(/<@&(\d+)>/g, (_match, id) => `@${roleNames.get(id) || "역할"}`);
}

if (!token || !channelIds.length || !guildId) {
  throw new Error("DISCORD_BOT_TOKEN, DISCORD_NEWS_CHANNEL_IDS and DISCORD_GUILD_ID are required.");
}

async function fetchDiscord(path) {
  const response = await fetch(`https://discord.com/api/v10${path}`, {
    headers: {
      Authorization: `Bot ${token}`,
      "User-Agent": "RSS-MOTD-News-Sync/1.0"
    }
  });
  if (!response.ok) {
    throw new Error(`Discord API request failed for ${path}: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

const roles = await fetchDiscord(`/guilds/${guildId}/roles`);
const roleNames = new Map(roles.map(role => [role.id, role.name]));

const channels = await Promise.all(channelIds.map(async channelId => {
  const [channel, messages] = await Promise.all([
    fetchDiscord(`/channels/${channelId}`),
    fetchDiscord(`/channels/${channelId}/messages?limit=${limit}`)
  ]);
  return {
    id: channelId,
    name: cleanDiscordText(channel.name) || channelId,
    messages
  };
}));

const memberIds = [...new Set(channels.flatMap(channel => channel.messages.flatMap(message => [
  message.author?.id,
  ...(message.mentions || []).map(mention => mention.id)
]).filter(Boolean)))];
const memberNames = new Map((await Promise.all(memberIds.map(async memberId => {
  try {
    const member = await fetchDiscord(`/guilds/${guildId}/members/${memberId}`);
    return [memberId, member.nick || ""];
  } catch (_error) {
    return [memberId, ""];
  }
}))).filter(([, name]) => name));

const items = channels.flatMap(channel => channel.messages
  .filter(message => [0, 19].includes(message.type) && (message.content?.trim() || message.embeds?.length))
  .map(message => {
    const resolvedMessageText = resolveDiscordMentions(message.content, message, roleNames, memberNames);
    const messageText = cleanDiscordText(resolvedMessageText);
    const embed = message.embeds?.[0] || {};
    const embedTitle = cleanDiscordText(resolveDiscordMentions(embed.title, message, roleNames, memberNames));
    const embedDescription = cleanDiscordText(resolveDiscordMentions(embed.description, message, roleNames, memberNames));
    if (!messageText && !embedTitle && !embedDescription) return null;

    const { title, content } = convertDiscordAnnouncement({
      rawContent: message.content,
      resolvedContent: resolvedMessageText,
      embedTitle,
      embedDescription
    });

    const attachments = (message.attachments || []).map(attachment => ({
      filename: attachment.filename,
      url: attachment.url,
      contentType: attachment.content_type || ""
    }));
    if (embed.image?.url) {
      attachments.push({ filename: embed.title || "embed-image", url: embed.image.url, contentType: "image/unknown" });
    }

    return {
      id: message.id,
      title,
      content,
      publishedAt: message.timestamp,
      editedAt: message.edited_timestamp || null,
      author: memberNames.get(message.author?.id) || message.member?.nick || message.author?.global_name || message.author?.username || "Discord",
      channelId: channel.id,
      channelName: channel.name,
      url: `https://discord.com/channels/${guildId}/${channel.id}/${message.id}`,
      attachments
    };
  })
  .filter(Boolean))
  .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

const updatedAt = items.reduce((latest, item) => {
  const candidate = item.editedAt || item.publishedAt;
  if (!candidate) return latest;
  return !latest || new Date(candidate) > new Date(latest) ? candidate : latest;
}, null);

const output = {
  version: 1,
  updatedAt,
  source: "discord",
  guildId,
  channels: channels.map(({ id, name }) => ({ id, name })),
  items
};

await writeFile(new URL("../news.json", import.meta.url), `${JSON.stringify(output, null, 2)}\n`, "utf8");
console.log(`Synced ${items.length} Discord announcements from ${channels.length} channels.`);
