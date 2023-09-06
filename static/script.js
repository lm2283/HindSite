document.getElementById('resize-forms').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const action = e.submitter.getAttribute('formaction');  // Get the action from the clicked button

    try {
        const response = await fetch(action, {
            method: 'POST',
            body: formData
        });

        let filename = '';
        if (action.endsWith('/converter')) {
            filename = 'converted_resized_output.zip';
        } else if (action.endsWith('/resizer')) {
            filename = 'resized_output.zip';
        }

        if (response.ok) {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('Error processing files.');
        }
    } catch (error) {
        console.error('There was an error processing the files.', error);
    }
});

document.getElementById('rename-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch(e.target.action, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'renamed_output.zip';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('Error renaming files.');
        }
    } catch (error) {
        console.error('There was an error renaming the files.', error);
    }
});

document.getElementById('watermark-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch(e.target.action, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'watermarked_output.zip';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('Error uploading file.');
        }
    } catch (error) {
        console.error('There was an error uploading the file.', error);
    }
});

document.getElementById('grouper-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const action = e.submitter.getAttribute('formaction');  // Get the action from the clicked button
    let filename = '';

    if (action.endsWith('/grouper')) {
        filename = 'grouped_images.zip';
    } else if (action.endsWith('/reorganize')) {
        filename = 'reorganized_images.zip';
    }

    try {
        const response = await fetch(action, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('Error processing files.');
        }
    } catch (error) {
        console.error('There was an error processing the files.', error);
    }
});

document.getElementById('pdf-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch(e.target.action, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'pages.zip';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('Error converting PDF to images.');
        }
    } catch (error) {
        console.error('There was an error converting the PDF to images.', error);
    }
});