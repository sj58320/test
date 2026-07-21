import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const commands = JSON.parse(
  await readFile(new URL("../data/commands.json", import.meta.url), "utf8")
);

const sound = commands.pages
  .find(page => page.id === "basic")
  ?.sections.find(section => section.title.en === "Sound");

test("adds the knife attack sound toggle to the sound commands", () => {
  assert.ok(sound);

  const matches = sound.commands.filter(item => item.command === "/knifesound");
  assert.equal(matches.length, 1);
  assert.deepEqual(matches[0].description, {
    ko: "다른 플레이어의 칼 공격음을 ON/OFF",
    en: "Toggle other players' knife attack sounds",
    jp: "他のプレイヤーのナイフ攻撃音をON/OFF"
  });
});
