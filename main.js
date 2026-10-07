/**
 * FoodEase – main.js
 * Comprehensive client-side interactivity:
 * - Dynamic AJAX Cart (Add, Increment, Decrement, Remove, Clear)
 * - Real-time Navbar & Sidebar Cart Badge Updates
 * - Restaurant mismatch handling
 * - Toast Notification System
 * - User Menu Dropdown Toggle
 * - Interactive Promo Code Application
 */

document.addEventListener("DOMContentLoaded", () => {
    // ------------------------------------------------------------------------
    // User Menu Dropdown Toggle
    // ------------------------------------------------------------------------
    const userToggle = document.getElementById("userMenuToggle");
    const userDropdown = document.getElementById("userDropdownMenu");

    if (userToggle && userDropdown) {
        userToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle("show");
            const chevron = userToggle.querySelector(".nav-chevron");
            if (chevron) {
                chevron.style.transform = userDropdown.classList.contains("show") ? "rotate(180deg)" : "rotate(0)";
            }
        });

        document.addEventListener("click", (e) => {
            if (!userDropdown.contains(e.target) && !userToggle.contains(e.target)) {
                userDropdown.classList.remove("show");
                const chevron = userToggle.querySelector(".nav-chevron");
                if (chevron) chevron.style.transform = "rotate(0)";
            }
        });
    }

    // ------------------------------------------------------------------------
    // Auto-dismiss Flash Alerts
    // ------------------------------------------------------------------------
    const flashToasts = document.querySelectorAll(".toast");
    flashToasts.forEach((toast) => {
        setTimeout(() => {
            toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            toast.style.opacity = "0";
            toast.style.transform = "translateX(20px)";
            setTimeout(() => toast.remove(), 400);
        }, 4500);
    });
});

// ----------------------------------------------------------------------------
// Floating Dynamic Toast Notification
// ----------------------------------------------------------------------------
function showDynamicToast(message, icon = "fa-bag-shopping") {
    const anchor = document.getElementById("dynamicToastAnchor");
    if (!anchor) return;

    const toast = document.createElement("div");
    toast.className = "dyn-toast";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    anchor.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        toast.style.opacity = "0";
        toast.style.transform = "translateY(15px)";
        setTimeout(() => toast.remove(), 300);
    }, 2800);
}

// ----------------------------------------------------------------------------
// Cart Badge Update Helper
// ----------------------------------------------------------------------------
function updateCartBadge(count) {
    const badge = document.getElementById("cartCountBadge");
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.style.display = "inline-flex";
            badge.style.animation = "none";
            badge.offsetHeight; /* trigger reflow */
            badge.style.animation = "bounceIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
        } else {
            badge.style.display = "none";
        }
    }

    const sidebarCount = document.getElementById("sidebarCartCount");
    if (sidebarCount) {
        sidebarCount.textContent = `${count} items`;
    }
}

// ----------------------------------------------------------------------------
// AJAX: Add to Cart
// ----------------------------------------------------------------------------
async function addToCart(itemId, clearMismatch = false) {
    try {
        const response = await fetch("/api/cart/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: itemId, clear_mismatch: clearMismatch })
        });

        const data = await response.json();

        if (response.status === 409 && data.mismatch) {
            const confirmClear = confirm(
                "Your bag already contains dishes from another restaurant.\n\nWould you like to clear your existing bag and start a fresh order from this restaurant?"
            );
            if (confirmClear) {
                return addToCart(itemId, true);
            }
            return;
        }

        if (data.success) {
            // Update button/stepper state on dish card
            const controlWrapper = document.querySelector(`.dish-qty-control-wrapper[data-item-id="${itemId}"]`);
            if (controlWrapper) {
                const addBtn = controlWrapper.querySelector(".btn-add-to-cart");
                const stepper = controlWrapper.querySelector(".qty-stepper");
                const qtySpan = controlWrapper.querySelector(".stepper-count");

                if (addBtn) addBtn.classList.add("hidden-btn");
                if (stepper) stepper.classList.remove("hidden-stepper");
                if (qtySpan) qtySpan.textContent = data.quantity;
            }

            // Update badge & trigger notification
            updateCartBadge(data.cart_count);
            showDynamicToast(data.message, "fa-circle-check");

            // Update sidebar state if on restaurant page
            updateSidebarPreview(data.cart_count);
        } else {
            alert(data.error || "Unable to add dish to cart.");
        }
    } catch (err) {
        console.error("Cart add error:", err);
    }
}

// ----------------------------------------------------------------------------
// AJAX: Update Cart Item (Increase, Decrease, Remove)
// ----------------------------------------------------------------------------
async function updateCartItem(itemId, action) {
    try {
        const response = await fetch("/api/cart/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: itemId, action: action })
        });

        const data = await response.json();

        if (data.success) {
            // Update Stepper on Restaurant Page
            const controlWrapper = document.querySelector(`.dish-qty-control-wrapper[data-item-id="${itemId}"]`);
            if (controlWrapper) {
                const addBtn = controlWrapper.querySelector(".btn-add-to-cart");
                const stepper = controlWrapper.querySelector(".qty-stepper");
                const qtySpan = controlWrapper.querySelector(".stepper-count");

                if (data.quantity <= 0) {
                    if (stepper) stepper.classList.add("hidden-stepper");
                    if (addBtn) addBtn.classList.remove("hidden-btn");
                } else {
                    if (qtySpan) qtySpan.textContent = data.quantity;
                }
            }

            // If on the Cart Page, update table rows & totals
            const cartRow = document.getElementById(`cartRow-${itemId}`);
            if (cartRow) {
                if (data.quantity <= 0) {
                    cartRow.style.transition = "opacity 0.25s, transform 0.25s";
                    cartRow.style.opacity = "0";
                    cartRow.style.transform = "translateX(-15px)";
                    setTimeout(() => {
                        cartRow.remove();
                        if (data.cart_count === 0) {
                            window.location.reload();
                        }
                    }, 250);
                } else {
                    const rowQty = document.getElementById(`itemQty-${itemId}`);
                    const rowSubtotal = document.getElementById(`rowSubtotal-${itemId}`);
                    if (rowQty) rowQty.textContent = data.quantity;
                }

                // Update summary amounts on Cart Page
                const subEl = document.getElementById("summarySubtotal");
                const delEl = document.getElementById("summaryDelivery");
                const taxEl = document.getElementById("summaryTax");
                const totEl = document.getElementById("summaryGrandTotal");

                if (subEl) subEl.textContent = `₹${Math.round(data.subtotal)}`;
                if (delEl) {
                    delEl.innerHTML = data.delivery_fee === 0 ? '<span class="text-green font-bold">FREE</span>' : `₹${Math.round(data.delivery_fee)}`;
                }
                if (taxEl) taxEl.textContent = `₹${Math.round(data.tax)}`;
                if (totEl) totEl.textContent = `₹${Math.round(data.total)}`;
            }

            // Update badge & sidebar
            updateCartBadge(data.cart_count);
            updateSidebarPreview(data.cart_count);

            if (action === "increase") showDynamicToast("Item added", "fa-plus");
            if (action === "decrease") showDynamicToast("Item quantity updated", "fa-minus");
            if (action === "remove") showDynamicToast("Item removed from bag", "fa-trash");
        }
    } catch (err) {
        console.error("Cart update error:", err);
    }
}

// ----------------------------------------------------------------------------
// AJAX: Clear Cart
// ----------------------------------------------------------------------------
async function clearCart() {
    if (!confirm("Are you sure you want to empty your entire bag?")) return;
    try {
        const response = await fetch("/api/cart/clear", { method: "POST" });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        }
    } catch (err) {
        console.error("Cart clear error:", err);
    }
}

// ----------------------------------------------------------------------------
// Sidebar Cart Helper on Restaurant Page
// ----------------------------------------------------------------------------
function updateSidebarPreview(cartCount) {
    const sidebarBody = document.getElementById("sidebarCartBody");
    if (!sidebarBody) return;

    if (cartCount > 0) {
        sidebarBody.innerHTML = `
            <p class="sidebar-ready-msg">You have items waiting in your bag.</p>
            <div class="free-delivery-indicator">
                <i class="fa-solid fa-truck-fast"></i>
                <span>Order over ₹500 for Free Delivery!</span>
            </div>
            <a href="/cart" class="btn-sidebar-checkout">
                <span>Review Bag & Checkout</span>
                <i class="fa-solid fa-arrow-right"></i>
            </a>
        `;
    } else {
        sidebarBody.innerHTML = `
            <div class="sidebar-empty-cart">
                <i class="fa-solid fa-basket-shopping empty-basket-icon"></i>
                <p>Your basket is empty</p>
                <span class="subtext">Add flavorful items from the menu to build your order!</span>
            </div>
        `;
    }
}

// ----------------------------------------------------------------------------
// Promo Code Application
// ----------------------------------------------------------------------------
function applyPromoCode() {
    const input = document.getElementById("couponInput");
    const msg = document.getElementById("couponMessage");
    const discountRow = document.getElementById("discountRow");
    const summaryDiscount = document.getElementById("summaryDiscount");
    const grandTotalEl = document.getElementById("summaryGrandTotal");
    const subtotalEl = document.getElementById("summarySubtotal");

    if (!input || !msg) return;

    const code = input.value.trim().toUpperCase();

    if (code === "EASE20") {
        msg.style.color = "var(--success)";
        msg.textContent = "🎉 Coupon EASE20 applied! 20% discount added.";

        if (subtotalEl && grandTotalEl) {
            const rawSub = parseFloat(subtotalEl.textContent.replace("₹", "")) || 0;
            const discount = Math.round(rawSub * 0.20);
            if (discountRow) discountRow.style.display = "flex";
            if (summaryDiscount) summaryDiscount.textContent = `-₹${discount}`;

            const currentGrand = parseFloat(grandTotalEl.textContent.replace("₹", "")) || 0;
            const newGrand = Math.max(0, currentGrand - discount);
            grandTotalEl.textContent = `₹${Math.round(newGrand)}`;
        }
    } else if (!code) {
        msg.style.color = "var(--danger)";
        msg.textContent = "Please enter a promo code.";
    } else {
        msg.style.color = "var(--danger)";
        msg.textContent = "Invalid code. Use code EASE20 for 20% off!";
    }
}
