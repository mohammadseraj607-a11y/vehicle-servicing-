/**
 * Vehicle Service At Home - Main JavaScript
 */

// API Base URL
const API_BASE = '';

// DOM Elements
let bookingForm, contactForm, vehicleTypeSelect, vehicleBrandSelect, citySelect;
let problemDescription;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize elements
    bookingForm = document.getElementById('bookingForm');
    contactForm = document.getElementById('contactForm');
    vehicleTypeSelect = document.getElementById('vehicle_type');
    vehicleBrandSelect = document.getElementById('vehicle_brand');
    citySelect = document.getElementById('city');
    problemDescription = document.getElementById('problem_description');

    // Setup event listeners
    setupMobileMenu();
    setupBookingForm();
    setupContactForm();
    setupServiceFilters();
    loadCities();
    
    // Load initial data if on booking page
    if (vehicleTypeSelect) {
        loadBrands();
    }
});

// Mobile Menu Toggle
function setupMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('show');
        });
    }
}

// Select Vehicle Type (from home page)
function selectVehicleType(type) {
    window.location.href = '/booking?type=' + type;
}

// Load Brands based on Vehicle Type
function loadBrands() {
    if (!vehicleTypeSelect) return;
    
    vehicleTypeSelect.addEventListener('change', async function() {
        const type = this.value;
        
        // Clear current options
        vehicleBrandSelect.innerHTML = '<option value="">Select Brand</option>';
        
        if (!type) return;
        
        try {
            const response = await fetch(API_BASE + '/api/brands?type=' + type);
            const data = await response.json();
            
            const brands = type === 'car' ? data.cars : data.bikes;
            
            brands.forEach(brand => {
                const option = document.createElement('option');
                option.value = brand.id;
                option.textContent = brand.name;
                vehicleBrandSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading brands:', error);
        }
    });
}

// Load Cities
async function loadCities() {
    if (!citySelect) return;
    
    try {
        const response = await fetch(API_BASE + '/api/cities');
        const cities = await response.json();
        
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

// Setup Booking Form
function setupBookingForm() {
    if (!bookingForm) return;
    
    // AI Recommendation on problem description
    let debounceTimer;
    problemDescription.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (this.value.length > 10) {
                getServiceRecommendations(this.value);
            }
        }, 1000);
    });
    
    // Form submission
    bookingForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(bookingForm);
        const data = Object.fromEntries(formData.entries());
        
        // Add vehicle type to data
        data.vehicle_type = vehicleTypeSelect.value;
        
        // Validate pincode
        if (data.pincode && data.pincode.length !== 6) {
            alert('Please enter a valid 6-digit pincode');
            return;
        }
        
        try {
            const response = await fetch(API_BASE + '/api/book-service', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success modal
                document.getElementById('bookingId').textContent = result.booking_id;
                document.getElementById('successModal').classList.add('show');
                
                // Reset form
                bookingForm.reset();
                document.getElementById('aiRecommendations').style.display = 'none';
            } else {
                alert(result.error || 'Booking failed. Please try again.');
            }
        } catch (error) {
            console.error('Booking error:', error);
            alert('An error occurred. Please try again.');
        }
    });
}

// Get AI Service Recommendations
async function getServiceRecommendations(description) {
    const vehicleType = vehicleTypeSelect ? vehicleTypeSelect.value : 'car';
    
    try {
        const response = await fetch(API_BASE + '/api/predict-service', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: description,
                vehicle_type: vehicleType
            })
        });
        
        const result = await response.json();
        
        if (result.recommended_services && result.recommended_services.length > 0) {
            showRecommendations(result);
        }
    } catch (error) {
        console.error('Prediction error:', error);
    }
}

// Show Recommendations in UI
function showRecommendations(result) {
    const container = document.getElementById('aiRecommendations');
    const list = document.getElementById('recommendationList');
    
    if (!container || !list) return;
    
    list.innerHTML = '';
    
    result.recommended_services.forEach((service, index) => {
        const tag = document.createElement('span');
        tag.className = 'recommendation-tag' + (index === 0 ? ' primary' : '');
        tag.textContent = service;
        list.appendChild(tag);
    });
    
    container.style.display = 'block';
}

// Close Modal
function closeModal() {
    document.getElementById('successModal').classList.remove('show');
}

// Close modal on outside click
document.addEventListener('click', function(e) {
    const modal = document.getElementById('successModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Setup Contact Form
function setupContactForm() {
    if (!contactForm) return;
    
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(contactForm);
        const data = Object.fromEntries(formData.entries());
        
        // Show success message
        alert('Thank you for your message! We will get back to you soon.');
        
        // Reset form
        contactForm.reset();
    });
}

// Setup Service Filters
function setupServiceFilters() {
    const filterType = document.getElementById('filterType');
    const filterBrand = document.getElementById('filterBrand');
    const filterCity = document.getElementById('filterCity');
    
    if (!filterType) return;
    
    // Load brands for filter
    loadFilterBrands();
    
    // Filter event listeners
    filterType.addEventListener('change', function() {
        loadFilterBrands();
        loadServiceCenters();
    });
    
    filterBrand.addEventListener('change', loadServiceCenters);
    filterCity.addEventListener('change', loadServiceCenters);
    
    // Initial load
    loadServiceCenters();
}

// Load Brands for Filter
async function loadFilterBrands() {
    const filterType = document.getElementById('filterType');
    const filterBrand = document.getElementById('filterBrand');
    
    if (!filterType || !filterBrand) return;
    
    try {
        const response = await fetch(API_BASE + '/api/brands?type=' + filterType.value);
        const data = await response.json();
        
        filterBrand.innerHTML = '<option value="">All Brands</option>';
        
        const brands = filterType.value === 'car' ? data.cars : 
                      filterType.value === 'bike' ? data.bikes : 
                      [...data.cars, ...data.bikes];
        
        brands.forEach(brand => {
            const option = document.createElement('option');
            option.value = brand.id;
            option.textContent = brand.name;
            filterBrand.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading filter brands:', error);
    }
}

// Load Service Centers
async function loadServiceCenters() {
    const container = document.getElementById('serviceCentersList');
    const filterType = document.getElementById('filterType');
    const filterBrand = document.getElementById('filterBrand');
    const filterCity = document.getElementById('filterCity');
    
    if (!container) return;
    
    const params = new URLSearchParams();
    if (filterType) params.append('type', filterType.value);
    if (filterBrand && filterBrand.value) params.append('brand', filterBrand.value);
    if (filterCity && filterCity.value) params.append('city', filterCity.value);
    
    try {
        const response = await fetch(API_BASE + '/api/service-centers?' + params);
        const data = await response.json();
        
        container.innerHTML = '';
        
        const centers = [...data.bike_centers, ...data.car_centers];
        
        if (centers.length === 0) {
            container.innerHTML = '<p class="no-results">No service centers found.</p>';
            return;
        }
        
        centers.forEach(center => {
            const card = document.createElement('div');
            card.className = 'service-center-card';
            
            const brandName = center.brand.replace('_', ' ').toUpperCase();
            const services = center.services.slice(0, 4).map(s => 
                `<span class="service-tag">${s}</span>`
            ).join('');
            
            card.innerHTML = `
                <h4>${center.name}</h4>
                <div class="city"><i class="fas fa-map-marker-alt"></i> ${center.city}</div>
                <div class="services-list">${services}</div>
            `;
            
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading service centers:', error);
        container.innerHTML = '<p class="error">Error loading service centers.</p>';
    }
}

// Service Category Filter (Services Page)
document.addEventListener('DOMContentLoaded', function() {
    const categoryBtns = document.querySelectorAll('.category-btn');
    
    categoryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const category = this.dataset.category;
            
            // Update active button
            categoryBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Filter services
            const cards = document.querySelectorAll('.service-detail-card');
            cards.forEach(card => {
                if (category === 'all' || card.dataset.category === category || card.dataset.category === 'both') {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'red';
            isValid = false;
        } else {
            input.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Phone number validation
function validatePhone(phone) {
    const regex = /^[0-9]{10}$/;
    return regex.test(phone);
}

// Pincode validation
function validatePincode(pincode) {
    const regex = /^[0-9]{6}$/;
    return regex.test(pincode);
}

// Export functions for global use
window.selectVehicleType = selectVehicleType;
window.closeModal = closeModal;
