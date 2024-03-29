let c = 0;
let showLog = (str) => {
  c++;
  document.getElementById("info").innerHTML = str;
  setTimeout(function() {
    --c;
    if (!c) {
      document.getElementById("info").innerHTML = "";
    }
  }, 3000);
};

document.getElementById("message").addEventListener("input", function() {
  let cursorPosition = this.selectionStart;
  if (this.value.indexOf("\n") !== -1) {
    --cursorPosition;
  }
  this.value = this.value.replaceAll("\n", "").replaceAll("\r", "");
  this.setSelectionRange(cursorPosition, cursorPosition);
});

document.getElementById("send").addEventListener("click", function() {
  document.getElementById("info").innerText = "Submitting...";
  document.getElementById("send").setAttribute("disabled", "");

  fetch("/api/messages/post/{{USER}}", {
    "method": "POST",
    "body": JSON.stringify({
      "message": document.getElementById("message").value,
      "name": document.getElementById("name").value || "Anonymous"
    })
  }).then((response) => {
    if (response.status == 200) {
      showLog("Success!");
      document.getElementById("message").value = "";
    } else { showLog("Something went wrong!"); }
    document.getElementById("send").removeAttribute("disabled");
  }).catch((err) => {
    showLog("Something went wrong!");
    document.getElementById("send").removeAttribute("disabled");
  });
});
