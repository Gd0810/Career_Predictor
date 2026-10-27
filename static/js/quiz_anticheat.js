/*
Quiz anti-cheat controller.
Rules implemented:
  - Candidate cannot open a new tab / switch to another app from the test window.
  - Each violation (tab switch / window blur) shows a warning alert.
  - After 3 violations, the quiz auto-submits immediately.
  - Normal form submission disables listener to prevent false violation upon submit.
*/
function initQuizAntiCheat(options) {
  const maxViolations = options.maxViolations || 3;
  const onAutoSubmit = options.onAutoSubmit;
  const violationLabel = document.getElementById("violation-count");
  let violations = 0;
  let submitted = false;

  function registerViolation(reason) {
    if (submitted) return;
    violations += 1;
    if (violationLabel) violationLabel.innerText = violations;
    if (violations >= maxViolations) {
      submitted = true;
      alert("You left the test window " + violations + " times. The quiz will be auto-submitted now.");
      onAutoSubmit(violations, true);
    } else {
      alert(
        "Warning " + violations + "/" + maxViolations + ": " + reason +
        "\nDo not switch tabs or open other apps during the test, or it will auto-submit."
      );
    }
  }

  document.addEventListener("visibilitychange", function () {
    if (submitted) return;
    if (document.hidden) registerViolation("You switched tabs or minimized the window.");
  });

  window.addEventListener("blur", function () {
    if (submitted) return;
    registerViolation("The test window lost focus.");
  });

  document.addEventListener("contextmenu", function (e) {
    if (submitted) return;
    e.preventDefault();
  });

  document.addEventListener("keydown", function (e) {
    if (submitted) return;
    if (e.altKey && e.key === "Tab") registerViolation("Attempted to switch application (Alt+Tab).");
    if (e.ctrlKey && (e.key === "t" || e.key === "n")) e.preventDefault();
  });

  return {
    getViolations: () => violations,
    setSubmitted: () => { submitted = true; },
  };
}

function startQuizTimer(totalSeconds, displayEl, onExpire) {
  let remaining = totalSeconds;
  const tick = () => {
    const m = Math.floor(remaining / 60).toString().padStart(2, "0");
    const s = (remaining % 60).toString().padStart(2, "0");
    displayEl.innerText = m + ":" + s;
    if (remaining <= 0) {
      clearInterval(interval);
      onExpire();
      return;
    }
    remaining -= 1;
  };
  tick();
  const interval = setInterval(tick, 1000);
  return interval;
}
