import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const faq = JSON.parse(await readFile(new URL("../data/faq.json", import.meta.url), "utf8"));
const langSource = await readFile(new URL("../assets/js/lang.js", import.meta.url), "utf8");
const langContext = { window: {} };
vm.runInNewContext(langSource, langContext, { filename: "lang.js" });
const languages = langContext.window.LANG;

test("adds the voice chat volume FAQ as the fifth quick-start card", () => {
  assert.deepEqual(faq.quickStart[4], { type: "faq", id: "voice_chat_volume" });

  const item = faq.items.find(entry => entry.id === "voice_chat_volume");
  assert.ok(item);
  assert.equal(item.question.langKey, "faq_8");
  assert.equal(
    item.body.find(block => block.type === "inlineCode")?.value,
    "snd_voipvolume 2"
  );
});

test("provides Korean, English, and Japanese voice chat copy", () => {
  assert.deepEqual(
    {
      question: languages.ko.faq_8,
      answerStart: languages.ko.answer_8_1,
      answerEnd: languages.ko.answer_8_2
    },
    {
      question: "오더 (보이스챗) 목소리가 작아요..",
      answerStart: "콘솔에",
      answerEnd: "를 치시면 됩니다."
    }
  );

  ["en", "jp"].forEach(language => {
    ["faq_8", "answer_8_1", "answer_8_2"].forEach(key => {
      assert.equal(typeof languages[language][key], "string", `${language}.${key}`);
      assert.ok(languages[language][key].length > 0, `${language}.${key}`);
    });
  });
});
