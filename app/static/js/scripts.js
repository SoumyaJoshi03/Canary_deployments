document.addEventListener("DOMContentLoaded", () => {
    // Upload Form Handling
    const uploadForm = document.getElementById("upload-form");
    if (uploadForm) {
        const fileInput = document.getElementById("model");
        const errorMessage = document.getElementById("error-message");
        const successMessage = document.getElementById("success-message");
        const submitButton = document.getElementById("submit-button");
        const progressBar = document.getElementById("dynamic-progress");

        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append("model", fileInput.files[0]);

            const xhr = new XMLHttpRequest();
            xhr.open("POST", "/upload");

            xhr.upload.addEventListener("progress", (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = `${percent}%`;
                    progressBar.textContent = `${percent}%`;
                }
            });

            xhr.onload = () => {
                if (xhr.status === 200) {
                    window.location.href = "/success";
                } else {
                    errorMessage.textContent = "Upload failed: " + xhr.responseText;
                    errorMessage.classList.remove("d-none");
                }
                progressBar.style.width = "0%";
            };

            xhr.onerror = () => {
                errorMessage.textContent = "Upload failed. Please try again.";
                errorMessage.classList.remove("d-none");
                progressBar.style.width = "0%";
            };

            xhr.send(formData);
        });
    }

    // Dashboard Updates
    const fetchDashboardData = async () => {
        try {
            const response = await fetch("/api/model-stats");
            const data = await response.json();
            const now = new Date().toLocaleTimeString();

            document.getElementById("accuracy").textContent = `${data.accuracy}%`;
            document.getElementById("latency").textContent = `${data.latency}ms`;
            
            const v1Progress = document.getElementById("v1-progress");
            const v2Progress = document.getElementById("v2-progress");
            v1Progress.style.width = `${data.traffic_split}%`;
            v2Progress.style.width = `${100 - data.traffic_split}%`;

            document.querySelectorAll(".metric-timestamp span").forEach(el => {
                el.textContent = now;
            });
        } catch (error) {
            console.error("Dashboard update error:", error);
        }
    };

    if (window.location.pathname === "/dashboard") {
        fetchDashboardData();
        setInterval(fetchDashboardData, 5000);
    }
});
