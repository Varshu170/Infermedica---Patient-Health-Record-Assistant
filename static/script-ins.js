$(document).ready(function() {
    $('input[name="search_by"]').change(function() {
        var selected = $('input[name="search_by"]:checked').val();
        if (selected === 'insurance_name') {
            $('#input-label').text('Insurance Name:');
        } else if (selected === 'claim_id') {
            $('#input-label').text('Claim ID:');
        }
    });

    $('#search-form').on('submit', function(event) {
        event.preventDefault();
        var search_by = $('input[name="search_by"]:checked').val();
        var input_value = $('#search-input').val();

        var data = {};
        data['search_by'] = search_by;
        if (search_by === 'insurance_name') {
            data['insurance_name'] = input_value;
        } else if (search_by === 'claim_id') {
            data['claim_id'] = input_value;
        }

        $.ajax({
            type: 'POST',
            url: '/insurance',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                $('#result').html(response.description);
                $('#download-btn').show(); // Show the download button
            },
            error: function(response) {
                $('#result').text('No data found');
                $('#download-btn').hide(); // Hide the download button
            }
        });
    });

    $('#download-btn').on('click', function() {
        var description = $('#result').html();
        $.ajax({
            type: 'POST',
            url: '/download_pdf',
            contentType: 'application/json',
            data: JSON.stringify({ 'description': description }),
            xhrFields: {
                responseType: 'blob'
            },
            success: function(response) {
                var url = window.URL.createObjectURL(new Blob([response]));
                var a = document.createElement('a');
                a.href = url;
                a.download = 'patient_data.pdf';
                document.body.appendChild(a);
                a.click();
                a.remove();
            },
            error: function() {
                alert('Error downloading PDF');
            }
        });
    });
});
