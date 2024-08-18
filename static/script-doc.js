function toggleInputFields() {
            const conditionInput = document.getElementById('condition_input');
            const doctorInput = document.getElementById('doctor_name');
            const surgeryInput = document.getElementById('surgery_input');
            const searchType = document.querySelector('input[name="searchType"]:checked').value;

            conditionInput.style.display = searchType === 'condition' ? 'block' : 'none';
            doctorInput.style.display = searchType === 'doctor' ? 'block' : 'none';
            surgeryInput.style.display = searchType === 'surgery' ? 'block' : 'none';
        }

        function fetchPatientData() {
            const searchType = document.querySelector('input[name="searchType"]:checked').value;
            let url = '';
            let postData = {};

            if (searchType === 'condition') {
                const conditionName = document.getElementById('condition_name_select').value;
                if (conditionName) {
                    url = '/fetch_patient_by_condition';
                    postData = { condition_name: conditionName };
                }
            }
            else if(searchType === 'doctor'){
                  const doctorName = document.getElementById('doctor_name_select').value;
                  if(doctorName){
                   url = '/fetch_patient_by_doctor';
                    postData = { doctor_name: doctorName };
                   }

            }
            else if (searchType === 'surgery') {
                const surgeryName = document.getElementById('surgery_name_select').value;
                if (surgeryName) {
                    url = '/fetch_patient_by_surgery';
                    postData = { surgery_name: surgeryName };
                }
            }

            if (url) {
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(postData),
                })
                .then(response => response.json())
                .then(data => {
                    displayPatientData(data);
                })
                .catch(error => console.error('Error:', error));
            }
        }

        function displayPatientData(data) {
            const patientDataDiv = document.getElementById('patientData');
            patientDataDiv.innerHTML = '';

            if (data.description) {
                patientDataDiv.innerHTML = `<p>${data.description}</p>`;
            } else {
                data.forEach(patient => {
                    const patientInfo = `
                        <div>
                            <p><strong>ID:</strong> ${patient.id}</p>
                            <p><strong>Name:</strong> ${patient.name.first} ${patient.name.last}</p>
                            <p><strong>Age:</strong> ${patient.age}</p>
                            <p><strong>${patient.medical_history.surgeries ? 'Surgeries' : 'Conditions'}:</strong> ${JSON.stringify(patient.medical_history.surgeries || patient.medical_history.conditions, null, 2)}</p>
                        </div>
                        <hr>
                    `;
                    patientDataDiv.innerHTML += patientInfo;
                });
            }
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
