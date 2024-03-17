const video = document.getElementById('video');
const resultContainer = document.getElementById('result-container');
const eyeStatus = document.getElementById('eye-status');

let currentFacingMode = 'environment';
let stream;

function startCamera() {
    const constraints = { video: { facingMode: currentFacingMode } };
    navigator.mediaDevices.getUserMedia(constraints)
        .then(function (stream) {
            video.srcObject = stream;
            startEyeDetection();
        })
        .catch(function (error) {
            console.log("Something went wrong: " + error);
        });
}

function startEyeDetection() {
    // Thực hiện xử lý phát hiện mắt ở đây và cập nhật kết quả
    const intervalId = setInterval(function () {
        const eyeStatusResult = detectEyeStatus(); // Hàm detectEyeStatus cần được thay thế bằng phần logic của bạn

        // Cập nhật kết quả lên trang web
        eyeStatus.textContent = eyeStatusResult;
    }, 1000); // Cập nhật kết quả mỗi giây

    // Dừng việc cập nhật sau khi ngừng sử dụng máy ảnh
    video.onended = function () {
        clearInterval(intervalId);
    };
}

function detectEyeStatus() {
    // Thực hiện phát hiện trạng thái mắt ở đây và trả về kết quả (ví dụ: "Open" hoặc "Closed")
    // Thay vì chụp hình và xử lý ở đây, bạn có thể sử dụng server để xử lý và trả kết quả
    // Sau đó, bạn cần gửi kết quả từ server về và cập nhật trang web.

    // Ví dụ:
    const randomValue = Math.random(); // Giả lập kết quả ngẫu nhiên
    if (randomValue > 0.5) {
        return "Open";
    } else {
        return "Closed";
    }
}
