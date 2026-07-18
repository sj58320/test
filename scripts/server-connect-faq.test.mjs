import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const faq = JSON.parse(await readFile(new URL("../data/faq.json", import.meta.url), "utf8"));
const langSource = await readFile(new URL("../assets/js/lang.js", import.meta.url), "utf8");
const scriptSource = await readFile(new URL("../assets/js/script.js", import.meta.url), "utf8");
const styleSource = await readFile(new URL("../assets/css/style.css", import.meta.url), "utf8");
const langContext = { window: {} };
vm.runInNewContext(langSource, langContext, { filename: "lang.js" });
const languages = langContext.window.LANG;

const imagePaths = [
  "assets/images/guide/steam-view-game-servers.png",
  "assets/images/guide/cs2-play-server-browser.png",
  "assets/images/guide/steam-server-favorites-add.png",
  "assets/images/guide/steam-server-address.png"
];

test("defines the server connection FAQ with ordered images and copyable address", () => {
  const item = faq.items.find(entry => entry.id === "server_connect");
  assert.ok(item);
  assert.equal(item.question.langKey, "faq_7");
  assert.deepEqual(
    item.body.filter(block => block.type === "image").map(block => block.src),
    imagePaths
  );
  assert.deepEqual(
    item.body.find(block => block.id === "serverAddress"),
    {
      type: "code",
      id: "serverAddress",
      copy: true,
      value: "14.6.92.207:27015"
    }
  );
});

test("keeps Japanese server connection copy identical to English", () => {
  const keys = [
    "faq_7",
    "answer_7_intro",
    "answer_7_steam",
    "answer_7_cs2",
    "answer_7_favorites",
    "answer_7_address"
  ];
  keys.forEach(key => {
    assert.equal(typeof languages.en[key], "string", key);
    assert.ok(languages.en[key].length > 0, key);
    assert.equal(languages.jp[key], languages.en[key], key);
  });
});

test("includes all four approved screenshots", async () => {
  await Promise.all(imagePaths.map(imagePath => access(new URL(`../${imagePath}`, import.meta.url))));
});

test("loads FAQ images lazily and keeps server screenshots responsive", () => {
  assert.match(scriptSource, /img\.loading = "lazy"/);
  assert.match(scriptSource, /img\.decoding = "async"/);
  assert.match(scriptSource, /block\.className/);
  assert.match(styleSource, /\.server-connect-image img\s*\{[^}]*max-width:\s*100%/s);
});
