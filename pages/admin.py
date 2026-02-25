from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Product, Order, OrderItem, Payment, StockAlert


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'first_name', 'last_name', 'email', 'phone', 'created_at', 'get_total_orders']
    list_filter = ['created_at', 'city', 'state']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('System Information', {
            'fields': ('customer_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_orders(self, obj):
        return obj.get_total_orders()
    get_total_orders.short_description = 'Total Orders'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'name', 'sku', 'category', 'price', 'stock_quantity', 
                    'get_stock_status', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['product_id', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'sku', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'unit', 'is_active')
        }),
        ('System Information', {
            'fields': ('product_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_stock_status(self, obj):
        status = obj.get_stock_status()
        if status == "Out of Stock":
            color = 'red'
        elif status == "Low Stock":
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_stock_status.short_description = 'Stock Status'
    
    def save_model(self, request, obj, form, change):
        """Check for stock alerts after saving"""
        super().save_model(request, obj, form, change)
        StockAlert.check_and_create_alerts()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'get_total']
    readonly_fields = ['get_total']
    
    def get_total(self, obj):
        if obj.pk:
            return f"₱{obj.get_total_price():,.2f}"
        return "-"
    get_total.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'get_order_total', 'get_total_items', 
                    'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name', 'customer__email']
    readonly_fields = ['order_id', 'order_number', 'subtotal', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'notes')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'tax', 'discount', 'total')
        }),
        ('System Information', {
            'fields': ('order_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_order_total(self, obj):
        return f"₱{obj.total:,.2f}"
    get_order_total.short_description = 'Total'
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    def save_formset(self, request, form, formset, change):
        """Recalculate totals after saving order items"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        
        # Recalculate order totals
        if form.instance.pk:
            form.instance.calculate_totals()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'order', 'amount', 'payment_method', 
                    'payment_status', 'payment_date', 'created_at']
    list_filter = ['payment_method', 'payment_status', 'payment_date']
    search_fields = ['payment_number', 'order__order_number', 'transaction_id']
    readonly_fields = ['payment_id', 'payment_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_number', 'order', 'amount', 'payment_method', 'payment_status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'payment_date', 'notes')
        }),
        ('System Information', {
            'fields': ('payment_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_type', 'alert_status', 'stock_level_at_alert', 
                    'message', 'created_at']
    list_filter = ['alert_type', 'alert_status', 'created_at']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['alert_id', 'created_at', 'resolved_at']
    
    def has_add_permission(self, request):
        # Prevent manual creation of alerts
        return False
