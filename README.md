# RSS_MOTD
rss에서 사용하는 motd 웹페이지 파일로 현재는 정적 페이지로 구현.

한국어 , English , 日本語 , 中文으로 구현되어있음.

rss_motd.html = html 메인 html 파일(css 및 js 파일을 불러옴)
style.css = html에서 웹페이지를 구현할때 배경을 만들어줌. (상자같은거)
lang.js = 언어 파일
script.js = 클립보드 , 열기/닫기 , 목록 등.. 버튼에대한 스크립트 구현

==============================================================

추가 및 수정 시 참고사항

rss_motd.html 부분

양식만 지키면 쉬움
아래와 같은 주석 처리된 부분 아래쪽을 설정하면된다.

<!-- FAQ(Create) --> FAQ 부분

<!-- <details>
    <summary>
        <span data-lang="faq_4">문의/신고는 어디로 하나요?</span> -> 질문임
        <span class="chev" data-lang="toggle">열기/닫기</span> -> 버튼임
        </summary>
        <div class="answer"> -> 대답에대한 클래스임
        <a href="https://discord.com/channels/850664390779731978/1321861335520120882/1384827886946484245"
            target="_blank"
            rel="noopener noreferrer"
            data-lang="discord_link">
            디스코드 링크
        </a>
        <span data-lang="answer_4">로 들어와서 문의 및 신고 바랍니다.</span>
    </div>
</details> -->

질문글을 추가할때 lang에서 위의 주석에서 코드에서 faq_4 처럼 해당되는 노드를 추가해주고 answer_4로 마찬가지로 구현해준다음에 위와같이 만들면됨.

<!-- 마지막 업데이트 날짜 갱신(Update) --> 업데이트 마지막 날짜 갱신

<!-- 일반 사용자(Create) -->  명령어 리스트 추가 (일반 사용자)

<!-- <tr>
    <td><span class="cmd">!admins</span></td>  -> 명령어
    <td><span data-lang="cmd_1">접속중인 어드민 목록</span></td> -> 설명
    <td><span class="cmd">!admins</span></td> -> 예시
</tr> -->

명령어 리스트를 추가할때 위와 같다. lang에 node를 추가해주고 cmd_1자리에 넣어주면된다.

<!-- VIP(Create) --> -> 명령어 리스트 추가 (VIP 사용자)

일반 사용자 명령어 리스트 추가와 같음

이미지파일을 넣는 방식은 rss_motd.html에서 경로를 그대로 따라간다. 현재사용중인 폴더 (guide_image)

