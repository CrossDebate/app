/**
 * configuracoes.js
 *
 * Handles fetching, displaying, and saving user settings on the
 * configuracoes.html page. Interacts with the backend API for
 * settings management and model listing.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Configurações script loaded.");

    // --- DOM Element References ---
    // General Settings
    const languageSelect = document.getElementById('languageSelect');
    const timezoneSelect = document.getElementById('timezoneSelect');
    const dateFormatSelect = document.getElementById('dateFormatSelect');

    // Analysis, HoT, and Model Settings
    const defaultModelSelect = document.getElementById('defaultModelSelect');
    const analysisModeSelect = document.getElementById('analysisModeSelect');
    const hotUpdateFrequency = document.getElementById('hotUpdateFrequency');
    const hotInfluenceFactorSlider = document.getElementById('hotInfluenceFactor');
    const hotInfluenceFactorValue = document.getElementById('hotInfluenceFactorValue');
    const confidenceThresholdSlider = document.getElementById('confidenceThreshold');
    const confidenceThresholdValue = document.getElementById('confidenceThresholdValue');
    const maxResultsInput = document.getElementById('maxResults');

    // Security Settings
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const twoFactorToggle = document.getElementById('twoFactorToggle');

    // Action Buttons
    const saveSettingsButton = document.getElementById('saveSettingsButton');
    const resetSettingsButton = document.getElementById('resetSettingsButton');

    // --- Helper Functions ---

    /**
     * Fetches data from the backend API.
     * @param {string} endpoint - The API endpoint (e.g., '/api/settings/load').
     * @param {object} options - Fetch options (method, headers, body).
     * @returns {Promise<object>} - The JSON response data.
     * @throws {Error} - If the fetch operation fails or returns an error status.
     */
    const fetchData = async (endpoint, options = {}) => {
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                let errorMsg = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorMsg;
                } catch (e) { /* Ignore if response is not JSON */ }
                throw new Error(errorMsg);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            // Use showNotification if available (defined in interactivity.js/HTML)
            if (typeof showNotification === 'function') {
                showNotification(`Erro ao comunicar com o servidor: ${error.message}`, 'error');
            }
            throw error; // Re-throw for calling function to handle
        }
    };

    /**
     * Populates the model selection dropdown.
     */
    const populateModelSelect = async () => {
        if (!defaultModelSelect) return;
        try {
            const models = await fetchData('/api/models'); // Assuming this endpoint exists
            defaultModelSelect.innerHTML = '<option value="">Selecione um modelo padrão...</option>'; // Clear existing
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.path; // Use path or a unique ID
                option.textContent = model.title; // Display name
                defaultModelSelect.appendChild(option);
            });
            console.log("Model select populated.");
            // After populating, load settings which might select one of these
            loadSettings();
        } catch (error) {
            defaultModelSelect.innerHTML = '<option value="">Erro ao carregar modelos</option>';
            console.error("Failed to populate model select:", error);
        }
    };

    /**
     * Loads current settings and populates the form.
     */
    const loadSettings = async () => {
        console.log("Loading settings...");
        try {
            const settings = await fetchData('/api/settings/load'); // Endpoint to load settings

            if (languageSelect) languageSelect.value = settings.general?.language || 'pt';
            if (timezoneSelect) timezoneSelect.value = settings.general?.timezone || 'America/Sao_Paulo';
            if (dateFormatSelect) dateFormatSelect.value = settings.general?.dateFormat || 'dd/mm/yyyy';

            if (defaultModelSelect) defaultModelSelect.value = settings.analysis?.defaultModel || '';
            if (analysisModeSelect) analysisModeSelect.value = settings.analysis?.analysisMode || 'advanced';
            if (hotUpdateFrequency) hotUpdateFrequency.value = settings.analysis?.hotUpdateFrequency || 'realtime';

            if (hotInfluenceFactorSlider) {
                hotInfluenceFactorSlider.value = settings.analysis?.hotInfluenceFactor ?? 0.5;
                if (hotInfluenceFactorValue) hotInfluenceFactorValue.textContent = hotInfluenceFactorSlider.value;
            }
            if (confidenceThresholdSlider) {
                confidenceThresholdSlider.value = settings.analysis?.confidenceThreshold ?? 0.7;
                if (confidenceThresholdValue) confidenceThresholdValue.textContent = confidenceThresholdSlider.value;
            }
            if (maxResultsInput) maxResultsInput.value = settings.analysis?.maxResults || 50;

            if (twoFactorToggle) twoFactorToggle.checked = settings.security?.twoFactorEnabled || false;

            console.log("Settings loaded and form populated.");

        } catch (error) {
            console.error("Failed to load settings:", error);
             if (typeof showNotification === 'function') {
                 showNotification('Não foi possível carregar as configurações atuais.', 'error');
             }
        }
    };

    /**
     * Collects settings data from the form.
     * @returns {object} - An object containing all settings values.
     */
    const collectSettings = () => {
        const settings = {
            general: {
                language: languageSelect?.value,
                timezone: timezoneSelect?.value,
                dateFormat: dateFormatSelect?.value,
            },
            analysis: {
                defaultModel: defaultModelSelect?.value,
                analysisMode: analysisModeSelect?.value,
                hotUpdateFrequency: hotUpdateFrequency?.value,
                hotInfluenceFactor: parseFloat(hotInfluenceFactorSlider?.value),
                confidenceThreshold: parseFloat(confidenceThresholdSlider?.value),
                maxResults: parseInt(maxResultsInput?.value, 10),
            },
            security: {
                twoFactorEnabled: twoFactorToggle?.checked,
                // Password fields are handled separately for security
            }
        };
        console.log("Collected settings:", settings);
        return settings;
    };

    /**
     * Validates password fields.
     * @returns {boolean} - True if passwords are valid or not being changed, false otherwise.
     */
    const validatePasswords = () => {
        const newPass = newPasswordInput?.value;
        const confirmPass = confirmPasswordInput?.value;

        // Only validate if a new password is entered
        if (newPass || confirmPass) {
            if (!currentPasswordInput?.value) {
                 if (typeof showNotification === 'function') {
                    showNotification('Por favor, digite sua senha atual para alterar a senha.', 'warning');
                 }
                 return false;
            }
            if (newPass.length < 8) {
                 if (typeof showNotification === 'function') {
                    showNotification('A nova senha deve ter pelo menos 8 caracteres.', 'warning');
                 }
                return false;
            }
            if (newPass !== confirmPass) {
                 if (typeof showNotification === 'function') {
                    showNotification('As novas senhas não coincidem.', 'error');
                 }
                return false;
            }
        }
        return true;
    };

    /**
     * Handles saving the settings.
     */
    const handleSaveSettings = async () => {
        if (!validatePasswords()) {
            return; // Stop if password validation fails
        }

        saveSettingsButton.disabled = true;
        saveSettingsButton.textContent = 'Salvando...';

        const settingsData = collectSettings();
        const passwordData = {
            currentPassword: currentPasswordInput?.value,
            newPassword: newPasswordInput?.value,
        };

        // Only send password data if a new password was entered
        const payload = {
            settings: settingsData,
            ...( (passwordData.newPassword) ? { password: passwordData } : {} )
        };

        try {
            const result = await fetchData('/api/settings/save', { // Endpoint to save settings
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            console.log("Save settings response:", result);
            if (typeof showNotification === 'function') {
                showNotification('Configurações salvas com sucesso!', 'success');
            }
            // Clear password fields after successful save
            if (currentPasswordInput) currentPasswordInput.value = '';
            if (newPasswordInput) newPasswordInput.value = '';
            if (confirmPasswordInput) confirmPasswordInput.value = '';

        } catch (error) {
            console.error("Failed to save settings:", error);
            // Notification is shown by fetchData
        } finally {
            saveSettingsButton.disabled = false;
            saveSettingsButton.textContent = 'Salvar Configurações';
        }
    };

    /**
     * Handles resetting settings to default.
     */
    const handleResetSettings = async () => {
        if (!confirm('Tem certeza que deseja restaurar as configurações padrão? Esta ação não pode ser desfeita.')) {
            return;
        }

        resetSettingsButton.disabled = true;
        resetSettingsButton.textContent = 'Restaurando...';

        try {
            const result = await fetchData('/api/settings/reset', { method: 'POST' }); // Endpoint to reset
            console.log("Reset settings response:", result);
            if (typeof showNotification === 'function') {
                showNotification('Configurações restauradas para o padrão.', 'info');
            }
            // Reload settings from backend after reset
            await loadSettings();

        } catch (error) {
            console.error("Failed to reset settings:", error);
            // Notification is shown by fetchData
        } finally {
            resetSettingsButton.disabled = false;
            resetSettingsButton.textContent = 'Restaurar Padrões';
        }
    };

    // --- Event Listeners ---

    // Update slider value displays
    if (hotInfluenceFactorSlider && hotInfluenceFactorValue) {
        hotInfluenceFactorSlider.addEventListener('input', () => {
            hotInfluenceFactorValue.textContent = hotInfluenceFactorSlider.value;
        });
    }
    if (confidenceThresholdSlider && confidenceThresholdValue) {
        confidenceThresholdSlider.addEventListener('input', () => {
            confidenceThresholdValue.textContent = confidenceThresholdSlider.value;
        });
    }

    // Button listeners
    if (saveSettingsButton) {
        saveSettingsButton.addEventListener('click', handleSaveSettings);
    }
    if (resetSettingsButton) {
        resetSettingsButton.addEventListener('click', handleResetSettings);
    }

    // --- Initial Load ---
    populateModelSelect(); // Populate models first, then load settings

}); // End DOMContentLoaded
