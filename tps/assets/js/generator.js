
function set_click(show_button, hide_button, script_data) {
            hide_button.click(function () {
                this.style.display = "none";
                show_button[0].style.display = "block";
                script_data[0].style.display = "none";
            });

            show_button.click(function () {
                this.style.display = "none";
                hide_button[0].style.display = "block";
                script_data[0].style.display = "block";
            });
        }
