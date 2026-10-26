/**
 * Artisan - Drawer Cart interactivo y reactivo a 60fps
 * Cumple con WCAG AA, cero CLS y sincronización instantánea con /api/cart
 */
(function() {
    'use strict';

    const CART_API = {
        GET: '/api/cart',
        ADD: (id) => `/api/cart/add/${id}`,
        UPDATE: (id) => `/api/cart/update/${id}`,
        REMOVE: (id) => `/api/cart/remove/${id}`,
        CLEAR: '/api/cart/clear'
    };

    const FREE_SHIPPING_THRESHOLD = 150000; // $150.000 COP para envío gratis

    function formatCOP(amount) {
        const num = Math.round(Number(amount) || 0);
        return '$' + num.toLocaleString('es-CO') + ' COP';
    }

    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag && metaTag.content) return metaTag.content;
        const input = document.querySelector('input[name="csrf_token"]');
        if (input && input.value) return input.value;
        if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
        return '';
    }

    const ArtisanCart = {
        isOpen: false,
        isLoading: false,
        data: { items: [], total: 0, count: 0, csrf_token: '' },

        init: function() {
            this.cacheDom();
            this.bindEvents();
            this.fetchCart();
        },

        cacheDom: function() {
            this.backdrop = document.getElementById('cart-drawer-backdrop');
            this.drawer = document.getElementById('cart-drawer');
            this.closeBtn = document.getElementById('cart-drawer-close');
            this.itemsList = document.getElementById('drawer-cart-list');
            this.emptyState = document.getElementById('drawer-cart-empty');
            this.drawerFooter = document.getElementById('drawer-cart-footer');
            this.subtotalEl = document.getElementById('drawer-cart-subtotal');
            this.countBadge = document.getElementById('drawer-item-count');
            this.shippingText = document.getElementById('shipping-progress-text');
            this.shippingBar = document.getElementById('shipping-progress-bar');
            this.whatsappBtn = document.getElementById('drawer-whatsapp-btn');
            this.headerBadges = document.querySelectorAll('.cart-badge-count, #cart-count-badge');
        },

        bindEvents: function() {
            const self = this;

            // Botón de cerrar y backdrop
            if (this.closeBtn) {
                this.closeBtn.addEventListener('click', function() { self.close(); });
            }
            if (this.backdrop) {
                this.backdrop.addEventListener('click', function() { self.close(); });
            }

            // Checkout por WhatsApp desde el Drawer invocando backend /api/cart/checkout
            if (this.whatsappBtn) {
                this.whatsappBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (self.isLoading) return;
                    if (!self.data.items || self.data.items.length === 0) {
                        self.showNotification('Tu bolsa está vacía', 'info');
                        return;
                    }

                    self.isLoading = true;
                    self.whatsappBtn.classList.add('is-loading');
                    const token = getCsrfToken();

                    fetch('/api/cart/checkout', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': token,
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({})
                    })
                    .then(res => {
                        if (!res.ok) throw new Error('Error al procesar el pedido');
                        return res.json();
                    })
                    .then(data => {
                        if (data.success && data.whatsapp_url) {
                            self.data = { items: [], total: 0, count: 0, csrf_token: token };
                            self.render();
                            self.close();
                            window.location.href = data.whatsapp_url;
                        } else {
                            throw new Error(data.error || 'Error al procesar el pedido');
                        }
                    })
                    .catch(err => {
                        console.error('Checkout error:', err);
                        self.showNotification(err.message || 'Error al procesar el pedido por WhatsApp', 'error');
                    })
                    .finally(() => {
                        self.isLoading = false;
                        if (self.whatsappBtn) self.whatsappBtn.classList.remove('is-loading');
                    });
                });
            }

            // Teclado Escape
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && self.isOpen) {
                    self.close();
                }
            });

            // Botones que abren el carrito en el header o enlaces a /carrito
            document.addEventListener('click', function(e) {
                const openTrigger = e.target.closest('[data-open-cart], .btn-open-cart, a[href="/carrito"].open-drawer');
                if (openTrigger) {
                    e.preventDefault();
                    self.open();
                }
            });

            // Interceptar formularios clásicos de agregar al carrito para evitar recarga
            document.addEventListener('submit', function(e) {
                const form = e.target;
                if (form && form.matches('form[action*="/carrito/add/"]')) {
                    e.preventDefault();
                    const actionUrl = form.getAttribute('action');
                    const match = actionUrl.match(/\/carrito\/add\/(\d+)/);
                    if (match && match[1]) {
                        const prodId = match[1];
                        const qtyInput = form.querySelector('input[name="cantidad"]');
                        const qty = qtyInput ? parseInt(qtyInput.value, 10) || 1 : 1;
                        self.addItem(prodId, qty);
                    }
                }
            });

            // Interceptar clics en botones con data-add-to-cart
            document.addEventListener('click', function(e) {
                const addBtn = e.target.closest('[data-add-to-cart]');
                if (addBtn) {
                    e.preventDefault();
                    const prodId = addBtn.getAttribute('data-add-to-cart');
                    const qtyAttr = addBtn.getAttribute('data-quantity');
                    const qty = qtyAttr ? parseInt(qtyAttr, 10) || 1 : 1;
                    self.addItem(prodId, qty, addBtn);
                }
            });

            // Delegación de eventos dentro del drawer (stepper de cantidad y eliminar)
            if (this.itemsList) {
                this.itemsList.addEventListener('click', function(e) {
                    const removeBtn = e.target.closest('.drawer-item-remove');
                    if (removeBtn) {
                        e.preventDefault();
                        const id = removeBtn.getAttribute('data-id');
                        self.removeItem(id);
                        return;
                    }

                    const qtyPlus = e.target.closest('.qty-btn-plus');
                    if (qtyPlus) {
                        e.preventDefault();
                        const id = qtyPlus.getAttribute('data-id');
                        const currentQty = parseInt(qtyPlus.getAttribute('data-qty'), 10) || 1;
                        self.updateItem(id, currentQty + 1);
                        return;
                    }

                    const qtyMinus = e.target.closest('.qty-btn-minus');
                    if (qtyMinus) {
                        e.preventDefault();
                        const id = qtyMinus.getAttribute('data-id');
                        const currentQty = parseInt(qtyMinus.getAttribute('data-qty'), 10) || 1;
                        if (currentQty <= 1) {
                            self.removeItem(id);
                        } else {
                            self.updateItem(id, currentQty - 1);
                        }
                    }
                });

                this.itemsList.addEventListener('change', function(e) {
                    const input = e.target.closest('.drawer-qty-input');
                    if (input) {
                        const id = input.getAttribute('data-id');
                        const val = parseInt(input.value, 10);
                        if (isNaN(val) || val <= 0) {
                            self.removeItem(id);
                        } else {
                            self.updateItem(id, Math.min(val, 999));
                        }
                    }
                });
            }
        },

        open: function() {
            if (!this.drawer) return;
            this.isOpen = true;
            this.drawer.classList.add('is-open');
            this.drawer.setAttribute('aria-hidden', 'false');
            if (this.backdrop) {
                this.backdrop.classList.add('is-open');
                this.backdrop.setAttribute('aria-hidden', 'false');
            }
            document.body.classList.add('cart-drawer-locked');

            // Enfoque accesible al cerrar botón
            if (this.closeBtn) {
                setTimeout(() => { this.closeBtn.focus(); }, 120);
            }
        },

        close: function() {
            if (!this.drawer) return;
            this.isOpen = false;
            this.drawer.classList.remove('is-open');
            this.drawer.setAttribute('aria-hidden', 'true');
            if (this.backdrop) {
                this.backdrop.classList.remove('is-open');
                this.backdrop.setAttribute('aria-hidden', 'true');
            }
            document.body.classList.remove('cart-drawer-locked');
        },

        toggle: function() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        },

        fetchCart: function() {
            const self = this;
            fetch(CART_API.GET, {
                headers: { 'Accept': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                self.data = data;
                self.render();
            })
            .catch(err => {
                console.warn('Error al obtener estado inicial del carrito:', err);
            });
        },

        addItem: function(id, qty = 1, triggerEl = null) {
            const self = this;
            if (triggerEl) {
                triggerEl.classList.add('is-loading');
            }

            const token = getCsrfToken();
            const formData = new FormData();
            formData.append('cantidad', qty);
            formData.append('csrf_token', token);

            fetch(CART_API.ADD(id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(res => {
                if (!res.ok) throw new Error('Error al agregar producto');
                return res.json();
            })
            .then(data => {
                self.data = data;
                self.render();
                self.open();
                self.pulseBadges();
            })
            .catch(err => {
                console.error(err);
                self.showNotification('No se pudo agregar la pieza. Intenta de nuevo.', 'error');
            })
            .finally(() => {
                if (triggerEl) {
                    triggerEl.classList.remove('is-loading');
                }
            });
        },

        updateItem: function(id, qty) {
            const self = this;
            const token = getCsrfToken();
            const formData = new FormData();
            formData.append('cantidad', qty);
            formData.append('csrf_token', token);

            fetch(CART_API.UPDATE(id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(res => {
                if (!res.ok) throw new Error('Error al actualizar cantidad');
                return res.json();
            })
            .then(data => {
                self.data = data;
                self.render();
            })
            .catch(err => {
                console.error(err);
                self.showNotification('Error al modificar cantidad', 'error');
            });
        },

        removeItem: function(id) {
            const self = this;
            const token = getCsrfToken();
            const formData = new FormData();
            formData.append('csrf_token', token);

            fetch(CART_API.REMOVE(id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(res => {
                if (!res.ok) throw new Error('Error al eliminar artículo');
                return res.json();
            })
            .then(data => {
                self.data = data;
                self.render();
            })
            .catch(err => {
                console.error(err);
                self.showNotification('No se pudo eliminar el artículo', 'error');
            });
        },

        pulseBadges: function() {
            const badges = document.querySelectorAll('.cart-badge-count, #cart-count-badge, #drawer-item-count');
            badges.forEach(b => {
                b.classList.remove('badge-pulse');
                void b.offsetWidth; // force reflow
                b.classList.add('badge-pulse');
            });
        },

        render: function() {
            const items = this.data.items || [];
            const count = this.data.count || 0;
            const total = this.data.total || 0;

            // Actualizar contadores
            if (this.countBadge) this.countBadge.textContent = count;
            this.headerBadges.forEach(badge => {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-flex' : 'none';
            });

            // Actualizar total en subtotal
            if (this.subtotalEl) {
                this.subtotalEl.textContent = formatCOP(total);
            }

            // Actualizar barra de envío gratis
            if (this.shippingText && this.shippingBar) {
                if (total >= FREE_SHIPPING_THRESHOLD) {
                    this.shippingText.innerHTML = '<strong>¡Felicitaciones!</strong> Tienes Envío Gratis a Colombia';
                    this.shippingBar.style.width = '100%';
                    this.shippingBar.classList.add('is-complete');
                } else {
                    const remaining = FREE_SHIPPING_THRESHOLD - total;
                    const pct = Math.min(100, Math.round((total / FREE_SHIPPING_THRESHOLD) * 100));
                    this.shippingText.innerHTML = `Faltan <strong>${formatCOP(remaining)}</strong> para <strong>Envío Gratis</strong>`;
                    this.shippingBar.style.width = pct + '%';
                    this.shippingBar.classList.remove('is-complete');
                }
            }

            // Estado vacío vs lista poblada
            if (items.length === 0) {
                if (this.emptyState) this.emptyState.style.display = 'flex';
                if (this.itemsList) {
                    this.itemsList.style.display = 'none';
                    this.itemsList.innerHTML = '';
                }
                if (this.drawerFooter) this.drawerFooter.style.display = 'none';
                return;
            }

            if (this.emptyState) this.emptyState.style.display = 'none';
            if (this.drawerFooter) this.drawerFooter.style.display = 'block';

            if (this.itemsList) {
                this.itemsList.style.display = 'flex';
                this.itemsList.innerHTML = items.map(item => {
                    const imgUrl = item.imagen_url ? `/${item.imagen_url.replace(/^\//, '')}` : '/static/img/IMG_20260121_150438.webp';
                    const unitPrice = formatCOP(item.precio);
                    const subtotal = formatCOP(item.subtotal || item.precio * item.cantidad);

                    return `
                    <li class="drawer-item" data-id="${item.id}">
                        <div class="drawer-item-img-wrap">
                            <img src="${imgUrl}" alt="${escapeHtml(item.nombre)}" class="drawer-item-img" loading="lazy" onerror="this.src='/static/img/IMG_20260121_150438.webp'">
                        </div>
                        <div class="drawer-item-info">
                            <h4 class="drawer-item-name"><a href="/producto/${item.id}">${escapeHtml(item.nombre)}</a></h4>
                            <div class="drawer-item-unit-price">${unitPrice} c/u</div>
                            
                            <div class="drawer-item-actions">
                                <div class="drawer-qty-stepper" role="group" aria-label="Cantidad">
                                    <button type="button" class="qty-btn qty-btn-minus" data-id="${item.id}" data-qty="${item.cantidad}" aria-label="Disminuir cantidad">&minus;</button>
                                    <input type="number" class="drawer-qty-input" data-id="${item.id}" value="${item.cantidad}" min="1" max="999" aria-label="Cantidad para ${escapeHtml(item.nombre)}">
                                    <button type="button" class="qty-btn qty-btn-plus" data-id="${item.id}" data-qty="${item.cantidad}" aria-label="Aumentar cantidad">&plus;</button>
                                </div>
                                <button type="button" class="drawer-item-remove" data-id="${item.id}" aria-label="Eliminar ${escapeHtml(item.nombre)} de la bolsa">
                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                    <span>Eliminar</span>
                                </button>
                            </div>
                        </div>
                        <div class="drawer-item-subtotal">
                            ${subtotal}
                        </div>
                    </li>
                    `;
                }).join('');
            }

            // El checkout por WhatsApp se gestiona vía POST /api/cart/checkout
            if (this.whatsappBtn) {
                this.whatsappBtn.setAttribute('href', '#');
            }
        },

        showNotification: function(msg, type = 'info') {
            const container = document.getElementById('flash-container') || createFlashContainer();
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = msg;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 400);
            }, 3500);
        }
    };

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function createFlashContainer() {
        let el = document.getElementById('flash-container');
        if (!el) {
            el = document.createElement('div');
            el.id = 'flash-container';
            document.body.appendChild(el);
        }
        return el;
    }

    // Exportar a window
    window.ArtisanCart = ArtisanCart;

    // Inicializar al cargar el DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { ArtisanCart.init(); });
    } else {
        ArtisanCart.init();
    }
})();
