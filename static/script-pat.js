function getPatientData() {
    const queryType = document.querySelector('input[name="query_type"]:checked').value;
    let requestData = { query_type: queryType };
    
    if (queryType === "single") {
        requestData.id = document.getElementById('patient_id').value;
    } else {
        requestData.start_id = document.getElementById('start_id').value;
        requestData.end_id = document.getElementById('end_id').value;
    }

    fetch('/patients', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('patientData').innerHTML = data.description;
    });
}


function downloadPDF() {
    const description = document.getElementById('patientData').innerHTML;

    fetch('/download_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description: description }),
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `patient_data.pdf`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
    });
}
