
// 1. 탭 전환 및 URL 해시 지원
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");

function openTab(name, pushHash = true) {
  tabs.forEach(t => {
    const active = t.dataset.tab === name;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", active ? "true" : "false");
  });
  panels.forEach(p => p.classList.toggle("active", p.id === name));
  if (pushHash) location.hash = name;
}

tabs.forEach(tab => {
  tab.addEventListener("click", () => openTab(tab.dataset.tab));
});

window.addEventListener("load", () => {
  const hash = (location.hash || "").replace("#", "");
  if (hash === "faq" || hash === "cmds") openTab(hash, false);
  else openTab("faq", false); // 기본은 FAQ
});


// 2. GitHub 최신 커밋 날짜 반영 (현재 : 비활성화)
/*
async function setLastUpdateFromGitHub() {
  const owner = "sj58320";
  const repo  = "test";

  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/commits?per_page=1`);
    if (!res.ok) throw new Error(res.status);

    const data = await res.json();
    const iso = data[0]?.commit?.committer?.date;
    if (!iso) throw new Error("no date");

    const d = new Date(iso);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");

    document.getElementById("lastUpdate").textContent = `${yyyy}-${mm}-${dd}`;
  } catch (e) {
    console.warn("lastUpdate failed:", e);
  }
}
window.addEventListener("load", setLastUpdateFromGitHub);
*/


// 3. 다국어 스크립트
function setLanguage(lang) {
  // 텍스트 교체
  document.querySelectorAll("[data-lang]").forEach(el => {
    const key = el.dataset.lang;
    const value = window.LANG?.[lang]?.[key] || LANG?.[lang]?.[key]; 
    
    if (value != null) el.textContent = value;
  });

  // 버튼 상태 클래스 토글 (함수 내부로 격리)
  document.querySelectorAll(".langbtn").forEach(b => {
    b.classList.toggle("active", b.dataset.lang === lang);
  });

  // 선택한 언어 저장 및 HTML 문서속서를 반영
  localStorage.setItem("lang", lang);
  document.documentElement.lang = lang;
}

// 언어 버튼 클릭 이벤트 바인딩
document.querySelectorAll(".langbtn").forEach(btn => {
  btn.addEventListener("click", () => {
    setLanguage(btn.dataset.lang);
  });
});

// 로드 시 기존에 저장된언어 자동적용
window.addEventListener("load", () => {
  const saved = localStorage.getItem("lang") || "ko";
  setLanguage(saved);
});


// 4. 클립보드 명령어 복사 기능
function copyCode(button) {
  // 버튼 옆의 pre code 태그 안의 텍스트 가져오기
  const codeText = document.getElementById("bindCommands").innerText;

  // 클립보드 복사 실행
  navigator.clipboard.writeText(codeText).then(() => {
    // 복사 성공 시 버튼 텍스트 변경 및 클래스 추가
    button.textContent = "복사 완료!";
    button.classList.add("copied");

    // 2초 후에 원래 상태로 되돌리기
    setTimeout(() => {
      button.textContent = "복사하기";
      button.classList.remove("copied");
    }, 2000);
  }).catch(err => {
    console.error("복사 실패:", err);
    alert("복사에 실패했습니다. 수동으로 복사해주세요.");
  });
}