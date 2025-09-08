document.addEventListener("DOMContentLoaded", () => {
    const toggleWrapper = document.getElementById("toggleWrapper");
    const toggleOptions = document.querySelectorAll(".toggle-option");
    const toggleSlider = document.querySelector(".toggle-slider");

    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    toggleOptions.forEach((option, index) => {
        option.addEventListener("click", () => {
            // убрать active со всех
            toggleOptions.forEach(opt => opt.classList.remove("active"));
            option.classList.add("active");

            // сдвиг слайдера
            toggleSlider.style.left = index === 0 ? "0%" : "50%";

            // показать форму
            if (option.dataset.form === "login") {
                loginForm.classList.remove("hidden");
                registerForm.classList.add("hidden");
            } else {
                registerForm.classList.remove("hidden");
                loginForm.classList.add("hidden");
            }
        });
    });

    // Индикатор силы пароля
    const passwordInput = document.getElementById("registerPassword");
    const strengthBar = document.getElementById("strengthBar");

    if (passwordInput && strengthBar) {
        passwordInput.addEventListener("input", () => {
            const value = passwordInput.value;
            let strength = 0;

            if (value.length >= 6) strength++;
            if (/[A-Z]/.test(value)) strength++;
            if (/[0-9]/.test(value)) strength++;
            if (/[^A-Za-z0-9]/.test(value)) strength++;

            strengthBar.style.width = (strength * 25) + "%";

            if (strength <= 1) {
                strengthBar.style.background = "red";
            } else if (strength === 2) {
                strengthBar.style.background = "orange";
            } else if (strength === 3) {
                strengthBar.style.background = "yellow";
            } else if (strength === 4) {
                strengthBar.style.background = "limegreen";
            }
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
  // ваш уже существующий код переключения форм и проверки силы пароля

  // а теперь добавляем toggle «замок/открытый замок»
  document.querySelectorAll(".form-group .input-icon").forEach(icon => {
    icon.addEventListener("click", () => {
      const input = icon.parentElement.querySelector("input");
      if (!input || (input.type !== "password" && input.type !== "text")) return;

      if (input.type === "password") {
        input.type = "text";
        icon.textContent = "🔓";
      } else {
        input.type = "password";
        icon.textContent = "🔒";
      }
    });
  });
});
