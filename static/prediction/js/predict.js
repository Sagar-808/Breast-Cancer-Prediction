// JavaScript to handle image preview
document.getElementById("image").addEventListener("change", function (event) {
    const previewDiv = document.getElementById("image-preview");
    previewDiv.innerHTML = ""; // Clear previous preview

    const file = event.target.files[0]; // Get the selected file
    if (file) {
        const img = document.createElement("img"); // Create an image element
        img.src = URL.createObjectURL(file); // Create a blob URL for the image
        img.alt = "Uploaded Image Preview";
        previewDiv.appendChild(img); // Add the image to the preview div
    } else {
        previewDiv.innerHTML = "<p>No image uploaded yet.</p>";
    }
});
