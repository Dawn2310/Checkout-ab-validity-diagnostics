/* Chat client — POSTs to /api/chat, keeps short history. */
(function () {
  const body = document.getElementById("chatBody");
  const input = document.getElementById("chatInput");
  const send = document.getElementById("chatSend");
  const suggest = document.getElementById("suggest");
  const history = [];

  function addMsg(role, text, typing = false) {
    const div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "bot") + (typing ? " typing" : "");
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
    return div;
  }

  async function ask(question) {
    if (!question.trim()) return;
    addMsg("user", question);
    history.push({ role: "user", content: question });
    input.value = "";
    send.disabled = true;
    const typing = addMsg("bot", "Analysing…", true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question, history: history.slice(0, -1) }),
      });
      const data = await res.json();
      typing.remove();
      const reply = data.reply || data.error || "Không nhận được phản hồi.";
      addMsg("bot", reply);
      history.push({ role: "assistant", content: reply });
    } catch (err) {
      typing.remove();
      addMsg("bot", "⚠️ Lỗi kết nối: " + err.message);
    } finally {
      send.disabled = false;
      input.focus();
    }
  }

  send.addEventListener("click", () => ask(input.value));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") ask(input.value);
  });
  if (suggest) {
    suggest.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON") ask(e.target.textContent);
    });
  }
})();
