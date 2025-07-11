function updateClock() {
  const now = new Date();
  const options = {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  };

  const formatted = now.toLocaleString("tr-TR", options);
  const clockElem = document.getElementById("clock");
  if (clockElem) {
    clockElem.textContent = formatted;
  }
}

setInterval(updateClock, 1000);
updateClock();

document.addEventListener("DOMContentLoaded", function () {
  const carousel = document.getElementById("carousel");
  let cards = Array.from(carousel.children);

  function updateClasses() {
    cards.forEach((card, index) => {
      card.classList.remove("active", "left", "right", "hidden");

      if (index === 1) {
        card.classList.add("active");
      } else if (index === 0) {
        card.classList.add("left");
      } else if (index === 2) {
        card.classList.add("right");
      } else {
        card.classList.add("hidden");
      }
    });
  }

  function rotateLeft() {
    const last = cards.pop();
    cards.unshift(last);
    cards.forEach(c => carousel.appendChild(c)); // DOM'da sıralamayı değiştir
    updateClasses();
  }

  function rotateRight() {
    const first = cards.shift();
    cards.push(first);
    cards.forEach(c => carousel.appendChild(c)); // DOM'da sıralamayı değiştir
    updateClasses();
  }

  document.getElementById("prevBtn").addEventListener("click", rotateLeft);
  document.getElementById("nextBtn").addEventListener("click", rotateRight);

  updateClasses();
});
