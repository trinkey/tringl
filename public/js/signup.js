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

document.getElementById("toggle").addEventListener("click", function() {
  let password = document.getElementById("password");
  password.setAttribute("type", password.getAttribute("type") == "password" ? "text" : "password");
  document.getElementById("confirm").setAttribute("type", password.getAttribute("type"));
});

document.getElementById("submit").addEventListener("click", function() {
  let username = document.getElementById("username").value;
  let passhash = sha256(document.getElementById("password").value);
  let confhash = sha256(document.getElementById("confirm").value);

  if (passhash !== confhash) {
    showLog("Passwords don't match!");
  } else if (username && passhash != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") {
    fetch("/api/account/signup", {
      "method": "POST",
      "body": JSON.stringify({
        "username": username,
        "passhash": passhash,
        "captcha": captcha
      })
    }).then((response) => {
      if (response.status == 200) {
        // Continue
      } else if (response.status == 400) {
        showLog("Bad username or password. Make sure the username only uses a-z, 0-9, and underscores and the password isn't blank.")
      } else if (response.status == 401) {
        showLog("An account with this username already exists!");
        throw new Error("Account already exists");
      } else if (resposne.status == 403) {
        showLog("Session expired, reload the page and try again.");
        throw new Error("Captcha expired");
      } else {
        showLog("An unknown error occured. Status code " + response.status);
        throw new Error("Unknown error");
      }
      return response;
    }).then((response) => (
      response.json()
    )).then((json) => {
      localStorage.setItem("token", json.token);
      setCookie("token", json.token);
      window.location.href = "/messages";
    }).catch((err) => { throw err; });
  }
});
