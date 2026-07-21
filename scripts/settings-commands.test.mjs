import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const commands = JSON.parse(
  await readFile(new URL("../data/commands.json", import.meta.url), "utf8")
);

const utility = commands.pages
  .find(page => page.id === "basic")
  ?.sections.find(section => section.title.en === "Utility");

const expected = {
  "/setting": {
    ko: "개인 설정 메뉴를 엽니다.",
    en: "Open the personal settings menu.",
    jp: "個人設定メニューを開きます。"
  },
  "/recoil": {
    ko: "화면 반동 감소를 ON/OFF 합니다.",
    en: "Toggle reduced screen recoil.",
    jp: "画面の反動軽減をON/OFFします。"
  },
  "/svsetting": {
    ko: "현재 서버 설정을 출력합니다.",
    en: "Display the current server settings.",
    jp: "現在のサーバー設定を表示します。"
  }
};

test("separates personal, recoil, and server settings commands", () => {
  assert.ok(utility);

  Object.entries(expected).forEach(([command, description]) => {
    const matches = utility.commands.filter(item => item.command === command);
    assert.equal(matches.length, 1, command);
    assert.deepEqual(matches[0].description, description);
  });
});
