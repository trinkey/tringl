let c = 0;
let showLog = (str) => {
  c++;
  document.getElementById("info").innerHTML = str;
  setTimeout(function() {
    --c;
    if (!c) {
      document.getElementById("info").innerHTML = "";
    }
  }, 5000);
};

function clearMessages() {
  if (confirm("Are you sure you want to clear your messages? (This can NOT be undone!)")) {
    fetch("/api/messages/clear", {
      "method": "DELETE"
    }).then((request) => {
      loadMessages();
      showLog("Messages cleared!");
    }).catch((err) => {
      showLog("Something went wrong clearing your messages! Try again later?");
    });
  }
}

function loadMessages() {
  document.getElementById("output").setAttribute("style", "opacity: 25%;");
  fetch("/api/messages/list")
    .then((response) => (response.json()))
    .then((json) => {
      let output = "";

      for (let i = 0; i < json.length; i++) {
        output += `
        <div class="msg">
          <b>${escapeHTML(json[i].name)}</b>
          <span> - ${timeSince(json[i].time)} ago</span><br>
          ${escapeHTML(json[i].message)}
        </div><br>`;
      }

      document.getElementById("output").innerHTML = output;
      document.getElementById("output").removeAttribute("style");
    })
    .catch((err) => {
      showLog("Something went wrong loading the messages! Try again in a few moments...");
      throw err;
    });
}

loadMessages();
