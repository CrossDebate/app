/**
 * interactivity.js
 *
 * Handles general UI interactions for the CrossDebate platform,
 * including theme switching and sidebar toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Interactivity script loaded.");

    // --- Theme Toggling ---
    const themeToggleButton = document.getElementById('themeToggle');
    const themeIcon = themeToggleButton ? themeToggleButton.querySelector('i') : null;

    // Function to apply the theme based on saved preference or system preference
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            if (themeIcon) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            }
        } else {
            document.body.classList.remove('dark-theme');
            if (themeIcon) {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    };

    // Function to toggle the theme
    const toggleTheme = () => {
        const isDark = document.body.classList.toggle('dark-theme');
        const newTheme = isDark ? 'dark' : 'light';
        applyTheme(newTheme); // Update icon immediately
        localStorage.setItem('theme', newTheme); // Save preference
        console.log(`Theme toggled to: ${newTheme}`);
    };

    // Initialize theme on load
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    applyTheme(initialTheme);

    // Add event listener to the toggle button
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', toggleTheme);
    } else {
        console.warn("Theme toggle button (#themeToggle) not found.");
    }

    // --- Sidebar Toggling ---
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarToggleButton = document.querySelector('.sidebar-toggle'); // Assuming a button with this class exists

    const toggleSidebar = () => {
        if (sidebar && mainContent) {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('with-collapsed-sidebar');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed); // Save state
            console.log(`Sidebar toggled: ${isCollapsed ? 'Collapsed' : 'Expanded'}`);

            // Optional: Change toggle button icon
            if (sidebarToggleButton) {
                const icon = sidebarToggleButton.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-chevron-left', !isCollapsed);
                    icon.classList.toggle('fa-chevron-right', isCollapsed);
                }
            }
        } else {
            console.warn("Sidebar or main content element not found for toggling.");
        }
    };

    // Initialize sidebar state
    const savedSidebarState = localStorage.getItem('sidebarCollapsed');
    if (sidebar && mainContent && savedSidebarState === 'true') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('with-collapsed-sidebar');
         // Optional: Update icon on load
         if (sidebarToggleButton) {
            const icon = sidebarToggleButton.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            }
        }
    }

    // Add event listener to the sidebar toggle button
    if (sidebarToggleButton) {
        sidebarToggleButton.addEventListener('click', toggleSidebar);
    } else {
        // If no dedicated button, maybe add logic for hover or other triggers if needed
        console.warn("Sidebar toggle button (.sidebar-toggle) not found.");
    }

    // --- Active Navigation Link ---
    // Highlight the active link in the sidebar based on the current page URL
    const currentPath = window.location.pathname.split('/').pop(); // Get the current HTML file name
    const navLinks = document.querySelectorAll('.sidebar ul li a');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath || (currentPath === '' && linkPath === 'index.html')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // --- Tooltip Handling (Simple Example) ---
    // Add basic tooltip functionality for elements with data-tooltip attribute
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        let tooltipElement = null;
        element.addEventListener('mouseenter', (event) => {
            const tooltipText = element.getAttribute('data-tooltip');
            if (!tooltipText) return;

            tooltipElement = document.createElement('div');
            tooltipElement.className = 'simple-tooltip';
            tooltipElement.textContent = tooltipText;
            document.body.appendChild(tooltipElement);

            // Position tooltip near the mouse
            tooltipElement.style.left = `${event.pageX + 10}px`;
            tooltipElement.style.top = `${event.pageY + 10}px`;
            tooltipElement.style.display = 'block'; // Show tooltip
        });

        element.addEventListener('mouseleave', () => {
            if (tooltipElement) {
                tooltipElement.remove();
                tooltipElement = null;
            }
        });

         element.addEventListener('mousemove', (event) => {
             if (tooltipElement) {
                tooltipElement.style.left = `${event.pageX + 10}px`;
                tooltipElement.style.top = `${event.pageY + 10}px`;
             }
         });
    });

    // Add CSS for the simple tooltip (could also be in style.css)
    const tooltipStyle = document.createElement('style');
    tooltipStyle.textContent = `
        .simple-tooltip {
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            z-index: 1002; /* Above other elements */
            pointer-events: none; /* Prevent tooltip from blocking mouse events */
            white-space: nowrap;
            display: none; /* Hidden by default */
        }
    `;
    document.head.appendChild(tooltipStyle);


    // --- Draggable Elements (Basic Implementation) ---
    // Note: For complex drag-and-drop, a library like interact.js or SortableJS is recommended.
    // This is a very basic example.
    document.querySelectorAll('.draggable').forEach(draggableElement => {
        let isDragging = false;
        let offsetX, offsetY;

        draggableElement.style.cursor = 'grab'; // Indicate draggability

        draggableElement.addEventListener('mousedown', (e) => {
            // Only allow dragging if the target isn't an input/button/link inside the draggable
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            isDragging = true;
            offsetX = e.clientX - draggableElement.getBoundingClientRect().left;
            offsetY = e.clientY - draggableElement.getBoundingClientRect().top;
            draggableElement.style.cursor = 'grabbing';
            draggableElement.style.position = 'relative'; // Or 'absolute' depending on context
            draggableElement.style.zIndex = '10'; // Bring to front while dragging
            // Prevent text selection while dragging
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            // Calculate new position relative to the parent container
            const parentRect = draggableElement.parentElement.getBoundingClientRect();
            let newX = e.clientX - parentRect.left - offsetX;
            let newY = e.clientY - parentRect.top - offsetY;

            // Basic boundary checks (optional, adjust as needed)
            // newX = Math.max(0, Math.min(newX, parentRect.width - draggableElement.offsetWidth));
            // newY = Math.max(0, Math.min(newY, parentRect.height - draggableElement.offsetHeight));

            draggableElement.style.left = `${newX}px`;
            draggableElement.style.top = `${newY}px`;
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                draggableElement.style.cursor = 'grab';
                draggableElement.style.zIndex = ''; // Reset z-index
            }
        });

         // Prevent dragging from interfering with text selection inside the element
         draggableElement.addEventListener('selectstart', (e) => {
             if (isDragging) {
                 e.preventDefault();
             }
         });
    });


}); // End DOMContentLoaded
