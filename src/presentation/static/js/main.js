// Main JavaScript for Protein Comparison App

document.addEventListener('DOMContentLoaded', function () {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // AlphaFold checkbox functionality
  const alphaFoldCheck = document.getElementById('alphaFoldCheck');
  const alphaFoldInfo = document.getElementById('alphaFoldInfo');

  if (alphaFoldCheck && alphaFoldInfo) {
    alphaFoldCheck.addEventListener('change', function () {
      if (this.checked) {
        alphaFoldInfo.style.display = 'block';
        alphaFoldInfo.classList.add('fade-in');
      } else {
        alphaFoldInfo.style.display = 'none';
        alphaFoldInfo.classList.remove('fade-in');
      }
    });
  }

  // Sequence validation functions
  const VALID_AMINO_ACIDS = 'ARNDCQEGHILKMFPSTWYV';

  function cleanSequence(sequence) {
    return sequence.replace(/\s+/g, '').toUpperCase();
  }

  function validateAminoAcids(sequence) {
    const invalidChars = [];
    for (let char of sequence) {
      if (!VALID_AMINO_ACIDS.includes(char) && !invalidChars.includes(char)) {
        invalidChars.push(char);
      }
    }
    return {
      isValid: invalidChars.length === 0,
      invalidChars: invalidChars,
    };
  }

  function findDifferences(original, mutated) {
    const differences = [];
    if (original.length !== mutated.length) {
      return differences;
    }

    for (let i = 0; i < original.length; i++) {
      if (original[i] !== mutated[i]) {
        differences.push({
          position: i + 1,
          original: original[i],
          mutated: mutated[i],
        });
      }
    }
    return differences;
  }

  // Real-time sequence validation
  function setupSequenceValidation() {
    const originalInput = document.getElementById('originalSequence');
    const mutatedInput = document.getElementById('mutatedSequence');
    const originalLength = document.getElementById('originalLength');
    const mutatedLength = document.getElementById('mutatedLength');
    const validationDisplay = document.getElementById('validationDisplay');
    const submitButton = document.querySelector('input[type="submit"]');

    if (!originalInput || !mutatedInput) return;

    function updateValidation() {
      const original = cleanSequence(originalInput.value);
      const mutated = cleanSequence(mutatedInput.value);

      // Update length displays
      if (originalLength) {
        originalLength.textContent = `Longitud: ${original.length} aminoácidos`;
      }
      if (mutatedLength) {
        mutatedLength.textContent = `Longitud: ${mutated.length} aminoácidos`;
      }

      if (!validationDisplay) return;

      let messages = [];
      let isValid = true;
      let alertClass = 'alert-success';

      if (original.length === 0 || mutated.length === 0) {
        validationDisplay.style.display = 'none';
        return;
      }

      // Validate amino acids
      const originalValidation = validateAminoAcids(original);
      const mutatedValidation = validateAminoAcids(mutated);

      if (!originalValidation.isValid) {
        messages.push(
          `❌ Caracteres inválidos en secuencia original: ${originalValidation.invalidChars.join(
            ', '
          )}`
        );
        isValid = false;
        alertClass = 'alert-danger';
      }

      if (!mutatedValidation.isValid) {
        messages.push(
          `❌ Caracteres inválidos en secuencia mutada: ${mutatedValidation.invalidChars.join(
            ', '
          )}`
        );
        isValid = false;
        alertClass = 'alert-danger';
      }

      if (!originalValidation.isValid || !mutatedValidation.isValid) {
        validationDisplay.style.display = 'block';
        validationDisplay.className = `alert ${alertClass}`;
        validationDisplay.innerHTML = messages.join('<br>');
        if (submitButton) submitButton.disabled = true;
        return;
      }

      // Check length
      if (original.length !== mutated.length) {
        messages.push(
          `❌ Diferentes longitudes: ${original.length} vs ${mutated.length}`
        );
        isValid = false;
        alertClass = 'alert-warning';
      } else {
        // Check differences
        const differences = findDifferences(original, mutated);

        if (differences.length === 0) {
          messages.push('⚠️ No hay diferencias entre las secuencias');
          isValid = false;
          alertClass = 'alert-warning';
        } else if (differences.length > 2) {
          messages.push(
            `❌ Demasiadas diferencias: ${differences.length} (máximo 2)`
          );
          isValid = false;
          alertClass = 'alert-danger';
        } else {
          const diffDescriptions = differences.map(
            (d) => `${d.original}${d.position}${d.mutated}`
          );
          messages.push(
            `✅ ${differences.length} diferencia(s): ${diffDescriptions.join(
              ', '
            )}`
          );
          alertClass = 'alert-success';
        }
      }

      if (messages.length > 0) {
        validationDisplay.style.display = 'block';
        validationDisplay.className = `alert ${alertClass}`;
        validationDisplay.innerHTML = messages.join('<br>');

        // Add animation
        validationDisplay.classList.add('validation-animation');
        setTimeout(() => {
          validationDisplay.classList.remove('validation-animation');
        }, 500);
      } else {
        validationDisplay.style.display = 'none';
      }

      // Enable/disable submit button
      if (submitButton) {
        submitButton.disabled = !isValid;
      }
    }

    // Add event listeners
    originalInput.addEventListener('input', updateValidation);
    mutatedInput.addEventListener('input', updateValidation);

    // Initial validation
    updateValidation();
  }

  // Setup form submission with loading state
  function setupFormSubmission() {
    const forms = document.querySelectorAll('form');

    forms.forEach((form) => {
      form.addEventListener('submit', function () {
        const submitButton = form.querySelector(
          'input[type="submit"], button[type="submit"]'
        );
        if (submitButton) {
          submitButton.disabled = true;
          const originalText = submitButton.value || submitButton.textContent;

          if (submitButton.tagName === 'INPUT') {
            submitButton.value = 'Procesando...';
          } else {
            submitButton.innerHTML =
              '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
          }

          // Re-enable after 10 seconds as fallback
          setTimeout(() => {
            submitButton.disabled = false;
            if (submitButton.tagName === 'INPUT') {
              submitButton.value = originalText;
            } else {
              submitButton.textContent = originalText;
            }
          }, 10000);
        }
      });
    });
  }

  // Auto-dismiss alerts
  function setupAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');

    alerts.forEach((alert) => {
      // Auto-dismiss success alerts after 5 seconds
      if (alert.classList.contains('alert-success')) {
        setTimeout(() => {
          const bsAlert = new bootstrap.Alert(alert);
          bsAlert.close();
        }, 5000);
      }
    });
  }

  // Copy sequence functionality
  function setupCopySequence() {
    const copyButtons = document.querySelectorAll('[data-copy-sequence]');

    copyButtons.forEach((button) => {
      button.addEventListener('click', function () {
        const targetId = this.getAttribute('data-copy-sequence');
        const targetElement = document.getElementById(targetId);

        if (targetElement) {
          const text = targetElement.textContent || targetElement.value;

          navigator.clipboard
            .writeText(text)
            .then(() => {
              // Show success feedback
              const originalIcon = this.innerHTML;
              this.innerHTML = '<i class="fas fa-check text-success"></i>';

              setTimeout(() => {
                this.innerHTML = originalIcon;
              }, 2000);
            })
            .catch((err) => {
              console.error('Error copying text: ', err);
              // Fallback for older browsers
              targetElement.select();
              document.execCommand('copy');
            });
        }
      });
    });
  }

  // Sequence formatting helpers
  function formatSequenceDisplay() {
    const sequenceDisplays = document.querySelectorAll('.sequence-display');

    sequenceDisplays.forEach((display) => {
      const sequence = display.textContent.replace(/\s+/g, '');
      let formatted = '';

      for (let i = 0; i < sequence.length; i += 10) {
        if (i > 0 && i % 50 === 0) {
          formatted += '\n';
        }
        formatted += sequence.substr(i, 10) + ' ';
      }

      display.textContent = formatted.trim();
    });
  }

  // Initialize all functionality
  setupSequenceValidation();
  setupFormSubmission();
  setupAlertAutoDismiss();
  setupCopySequence();
  formatSequenceDisplay();

  // Add smooth scrolling to anchors
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }
    });
  });

  // Add keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    // Ctrl+Enter to submit form
    if (e.ctrlKey && e.key === 'Enter') {
      const form = document.querySelector('form');
      if (form) {
        const submitButton = form.querySelector(
          'input[type="submit"]:not(:disabled)'
        );
        if (submitButton) {
          submitButton.click();
        }
      }
    }

    // Escape to clear validation display
    if (e.key === 'Escape') {
      const validationDisplay = document.getElementById('validationDisplay');
      if (validationDisplay && validationDisplay.style.display !== 'none') {
        validationDisplay.style.display = 'none';
      }
    }
  });
});

// Utility functions for external use
window.ProteinComparator = {
  validateSequence: function (sequence) {
    const VALID_AMINO_ACIDS = 'ARNDCQEGHILKMFPSTWYV';
    const cleaned = sequence.replace(/\s+/g, '').toUpperCase();

    for (let char of cleaned) {
      if (!VALID_AMINO_ACIDS.includes(char)) {
        return { valid: false, error: `Invalid amino acid: ${char}` };
      }
    }

    return { valid: true, sequence: cleaned };
  },

  compareSequences: function (original, mutated) {
    original = original.replace(/\s+/g, '').toUpperCase();
    mutated = mutated.replace(/\s+/g, '').toUpperCase();

    if (original.length !== mutated.length) {
      return {
        valid: false,
        error: `Different lengths: ${original.length} vs ${mutated.length}`,
      };
    }

    const differences = [];
    for (let i = 0; i < original.length; i++) {
      if (original[i] !== mutated[i]) {
        differences.push({
          position: i + 1,
          original: original[i],
          mutated: mutated[i],
        });
      }
    }

    return {
      valid: differences.length > 0 && differences.length <= 2,
      differences: differences,
      totalDifferences: differences.length,
    };
  },
};
