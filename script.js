const slider = document.getElementById("jellyRange");
const fill = document.getElementById("gooeyFill");
const thumb = document.getElementById("gooeyThumb");
const value = document.getElementById("jellyValue");

slider.oninput = function () {
    const percent = this.value + "%";
    fill.style.width = percent;
    thumb.style.left = `calc(${percent} - 19px)`;
    value.textContent = percent;
};
