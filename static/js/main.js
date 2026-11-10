// ResumeAI Main JavaScript

document.addEventListener('DOMContentLoaded', function () {

  // ── File Upload Drag & Drop ──────────────────────────────────────
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('resumeFile');
  const fileName = document.getElementById('fileName');
  const uploadBtn = document.getElementById('uploadBtn');

  if (dropZone && fileInput) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#4f46e5';
      dropZone.style.background = '#ede9fe';
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = '#c7d2fe';
      dropZone.style.background = '#f5f3ff';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#c7d2fe';
      dropZone.style.background = '#f5f3ff';
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        showFileName(files[0].name);
      }
    });

    fileInput.addEventListener('change', function () {
      if (this.files.length > 0) {
        showFileName(this.files[0].name);
      }
    });

    function showFileName(name) {
      fileName.textContent = '✅ ' + name;
      fileName.classList.remove('d-none');
      if (uploadBtn) {
        uploadBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Analyze Resume';
        uploadBtn.classList.add('btn-success');
        uploadBtn.classList.remove('btn-primary');
      }
    }
  }

  // ── Upload form loading state ────────────────────────────────────
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', function () {
      if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
      }
    });
  }

  // ── Auto-dismiss alerts ──────────────────────────────────────────
  document.querySelectorAll('.alert:not(.alert-info)').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // ── Animated progress bars ───────────────────────────────────────
  const animateBars = () => {
    document.querySelectorAll('.progress-bar[style*="width"]').forEach(bar => {
      const targetWidth = bar.style.width;
      bar.style.width = '0%';
      bar.style.transition = 'width 1.2s cubic-bezier(.4,0,.2,1)';
      setTimeout(() => { bar.style.width = targetWidth; }, 200);
    });
  };
  animateBars();

  // ── Role card selection visual ───────────────────────────────────
  document.querySelectorAll('.role-card').forEach(card => {
    card.addEventListener('click', function () {
      const radio = this.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  // ── Tooltip init ─────────────────────────────────────────────────
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

  // ── Counter animation for stat cards ────────────────────────────
  document.querySelectorAll('.stat-card .fs-2').forEach(el => {
    const target = parseInt(el.textContent);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.ceil(target / 30);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 40);
  });

  // ── Skill badge hover color ──────────────────────────────────────
  document.querySelectorAll('.skill-badge').forEach(badge => {
    badge.addEventListener('mouseenter', function () {
      this.style.background = 'linear-gradient(135deg, #dbeafe, #bfdbfe)';
      this.style.transform = 'scale(1.05)';
    });
    badge.addEventListener('mouseleave', function () {
      this.style.background = '';
      this.style.transform = '';
    });
  });

});
