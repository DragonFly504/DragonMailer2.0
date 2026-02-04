// Wait for DOM to be ready and check if elements exist
document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById("jellyRange");
    const fill = document.getElementById("gooeyFill");
    const thumb = document.getElementById("gooeyThumb");
    const value = document.getElementById("jellyValue");
    
    // Only set up slider if all elements exist
    if (slider && fill && thumb && value) {
        slider.oninput = function () {
            const percent = this.value + "%";
            fill.style.width = percent;
            thumb.style.left = `calc(${percent} - 19px)`;
            value.textContent = percent;
        };
    }
});
