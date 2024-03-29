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
});

document.getElementById("submit").addEventListener("click", function() {
  let username = document.getElementById("username").value;
  let passhash = sha256(document.getElementById("password").value);

  if (username && passhash != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") {
    fetch("/api/account/login", {
      "method": "POST",
      "body": JSON.stringify({
        "username": username,
        "passhash": passhash
      })
    }).then((response) => {
      if (response.status == 200) {
        // Continue
      } else if (response.status == 400) {
        showLog("Bad username or password. Make sure your username and password are both correct.")
      } else if (response.status == 401) {
        showLog("An account with this username doesn't exist!");
        throw new Error("Account doesn't exist");
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
