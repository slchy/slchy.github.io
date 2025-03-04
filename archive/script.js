let currentScreen = 1; // 当前屏幕编号
let isAnimating = false;
let disableScroll = false; // 滚轮事件禁用标识
const scrollDisableDuration = 5000; // 禁用滚轮事件的时间（毫秒）

// 检测是否为移动设备
document.addEventListener('DOMContentLoaded', () => {
  const isMobile = () => {
      return /Mobi|Android/i.test(navigator.userAgent);
  };

  if (isMobile()) {
      window.location.href = 'https://slchy.com/archive';
  }
});


window.addEventListener('wheel', function (event) {
    if (isAnimating || disableScroll) return;
    const screen1 = document.querySelector('.screen-1');
    const screen2 = document.querySelector('.screen-2');

    // 向下滚动，切换到界面二
    if (event.deltaY > 0 && currentScreen === 1) {
        isAnimating = true;
        currentScreen = 2;
        screen1.style.transform = 'translateY(-100vh)';
        screen2.style.transform = 'translateY(0)'; // 将第二屏幕移动到视口内
        setTimeout(() => {
          showDialogs();
          isAnimating = false; // 动画结束后重置状态
          disableScroll = true; // 禁用滚轮事件
          setTimeout(() => {
              disableScroll = false; // 在规定时间后重新启用滚轮事件
          }, scrollDisableDuration);
      }, 1000); // 等待过渡动画结束后显示对话框
    } 
    // 向上滚动，切换回界面一
    else if (event.deltaY < 0 && currentScreen === 2) {
        isAnimating = true;
        currentScreen = 1;
        screen1.style.transform = 'translateY(0)';
        screen2.style.transform = 'translateY(100vh)'; // 将第二屏幕移回到初始位置
        hideDialogs(); // 隐藏对话框
        setTimeout(() => {
            isAnimating = false; // 动画结束后重置状态
        }, 5000); // 等待过渡动画结束
    }
});

function showDialogs() {
  const dialogs = document.querySelectorAll('.dialog');
  const footerText = document.getElementById('footer-text');

  dialogs.forEach((dialog, index) => {
      setTimeout(() => {
          dialog.classList.add('show');
          // 在最后一个对话框显示后，显示底部文本
          if (index === dialogs.length - 1) {
              setTimeout(() => {
                  footerText.style.opacity = '1'; // 显示底部提示文字
              }, 1000); // 等待最后一个对话框动画结束
          }
      }, index * 1000); // 控制对话框显示间隔
  });
}

function hideDialogs() {
  const dialogs = document.querySelectorAll('.dialog');
  const footerText = document.getElementById('footer-text');

  dialogs.forEach((dialog) => {
      dialog.classList.remove('show');
      
  });
  
  // 隐藏底部提示文字
  footerText.style.opacity = '0';
}
