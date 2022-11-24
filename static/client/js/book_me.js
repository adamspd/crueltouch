function forceLower(strInput) {
    strInput.value = strInput.value.toLowerCase();
}

function forceTitle(str) {
    str.value = str.value.replace(/\w\S*/g, function (txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

function forceNumber(evt) {
    // replace all non-digit characters with empty strings
    evt.value = evt.value.replace(/\D/g, '');
    // replace all fake phone numbers with empty strings

}

function activate_date() {
    const birth_date = $('#id_desired_date');
    birth_date.attr('type', 'date')

    // add max
    let date = new Date();
    const new_date = date.getFullYear() + '-' + date.getMonth() + '-' + date.getDay();
    birth_date.attr('max', new_date)
}

function display() {
    const place = document.getElementById("id_place").value;
    const packages = document.getElementById("id_package").value;
    const session = document.getElementById("id_session_type").value;

    if (session !== "wOthers") {
        if (place === 'studio') {
            document.getElementById('note').innerHTML = "+40$ for studio rental";
            if (packages === "7") {
                document.getElementById('totalPrice').innerHTML = "Total: 220$";
            } else if (packages === "15") {
                document.getElementById('totalPrice').innerHTML = "Total: 325$";
            } else if (packages === "30") {
                document.getElementById('totalPrice').innerHTML = "Total: 460$";
            }
        } else if (place === 'outdoor') {
            document.getElementById('note').innerHTML = "";
            if (packages === "7") {
                document.getElementById('totalPrice').innerHTML = "Total: 220$";
            } else if (packages === "15") {
                document.getElementById('totalPrice').innerHTML = "Total: 325$";
            } else if (packages === "30") {
                document.getElementById('totalPrice').innerHTML = "Total: 460$";
            }
        } else if (place === 'orlando') {
            // if element packages doesn't contains value 3, append it
            let exists = false;
            $('#id_package  option').each(function () {
                if (this.value === "3") {
                    exists = true;
                }
            });
            if (!exists) {
                $('#id_package').append($('<option>', {
                    value: "3",
                    text: '3 photos'
                }));
            }
            document.getElementById('note').innerHTML = "+40$ if studio rental";
            if (packages === "3") {
                document.getElementById('totalPrice').innerHTML = "Total: 130$";
                document.getElementById('note').innerHTML = "Orlando ONLY. +40$ for studio rental";
                // style="color: red"
                document.getElementById('note').style.color = "red";
            } else if (packages === "7") {
                document.getElementById('totalPrice').innerHTML = "Total: 220$";
            } else if (packages === "15") {
                document.getElementById('totalPrice').innerHTML = "Total: 325$";
            } else if (packages === "30") {
                document.getElementById('totalPrice').innerHTML = "Total: 460$";
            }
        } else {
            document.getElementById('totalPrice').innerHTML = "";
            document.getElementById('note').innerHTML = "Contact me for specifics.";
        }
    } else {
        document.getElementById('totalPrice').innerHTML = "";
        document.getElementById('note').innerHTML = "Contact me for specifics.";
    }
}

// on ready
$(document).ready(function () {
    $("#id_package option[value='3']").remove();
    $(document).ready(function () {
        const date_input = $("#id_desired_date"); //our date input has the name "date"
        const container = $('.bootstrap-iso form').length > 0 ? $('.bootstrap-iso form').parent() : "body";
        // get tomorrow's date
        let date = new Date();
        date.setDate(date.getDate() + 1);
        const options = {
            showOn: "button",
            format: 'yyyy-mm-dd',
            showButtonPanel: true,
            changeMonth: true,
            changeYear: true,
            container: container,
            todayHighlight: true,
            autoclose: true,
            startDate: date,
            endDate: '+1y',
            inline: true,
            clearBtn: true,
        };
        date_input.datepicker(options);

    })
});