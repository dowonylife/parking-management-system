function startCapture(inputFieldId) {
  // 로딩 애니메이션 표시
  document.getElementById("loading-spinner").style.display = "block";

  // Fetch를 사용해 자동 감지 호출
  fetch('/capture')
      .then(response => response.json())
      .then(data => {
          // 로딩 애니메이션 숨기기
          document.getElementById("loading-spinner").style.display = "none";

          if (data.status === "success") {
              alert("번호판 인식 성공: " + data.plate);
              document.getElementById(inputFieldId).value = data.plate; // 입력 필드에 번호판 자동 입력
          } else {
              alert(data.message || "번호판 인식 실패");
          }
      })
      .catch(error => {
          // 로딩 애니메이션 숨기기
          document.getElementById("loading-spinner").style.display = "none";
          alert("Error: " + error);
      });
}

function startCapture(inputFieldId) {
  // 로딩 오버레이 표시
  document.getElementById("loading-overlay").style.display = "flex";

  fetch('/capture')
      .then(response => response.json())
      .then(data => {
          // 로딩 오버레이 숨기기
          document.getElementById("loading-overlay").style.display = "none";

          if (data.status === "success") {
              alert("번호판 인식 성공: " + data.plate);
              document.getElementById(inputFieldId).value = data.plate;
          } else {
              alert(data.message || "번호판 인식 실패");
          }
      })
      .catch(error => {
          // 로딩 오버레이 숨기기
          document.getElementById("loading-overlay").style.display = "none";
          alert("Error: " + error);
      });
}
