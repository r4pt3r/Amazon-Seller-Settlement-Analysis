import streamlit as st
import pandas as pd
import io
from PIL import Image, ImageDraw, ImageFont
import zipfile
from datetime import datetime

# Try to import barcode library
try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

# Page configuration
try:
    st.set_page_config(
        page_title="MRP Label Generator",
        page_icon="🏷️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    pass

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .step-header {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .variable-config {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables with proper defaults"""
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None
        
    if 'label_config' not in st.session_state:
        st.session_state.label_config = {
            'selected_variables': [],
            'variable_settings': {},
            'barcode_variable': '',
            'barcode_settings': {
                'height': 40, 
                'show_text': True, 
                'font_size': 10
            },
            'label_dimensions': {
                'width': 400, 
                'height': 200
            },
            'variable_order': []
        }

    if 'generated_labels' not in st.session_state:
        st.session_state.generated_labels = []

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏷️ MRP Label Generator</h1>
        <p>Upload Excel → Configure Variables → Generate Labels</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content based on page selection
    page = st.session_state.get('current_page', 'upload')
    
    if page == 'upload':
        upload_data_page()
    elif page == 'configure':
        configure_labels_page()
    elif page == 'preview':
        preview_design_page()
    elif page == 'generate':
        generate_labels_page()
    elif page == 'history':
        history_page()

def render_sidebar():
    """Render sidebar navigation"""
    st.sidebar.title("Workflow Steps")
    
    # Status indicators
    if st.session_state.uploaded_data is not None:
        st.sidebar.success("✅ Data Uploaded")
        st.sidebar.write(f"📊 {len(st.session_state.uploaded_data)} rows")
    else:
        st.sidebar.info("📤 Upload Excel file first")
    
    if st.session_state.label_config['selected_variables']:
        count = len(st.session_state.label_config['selected_variables'])
        st.sidebar.success(f"✅ {count} variables configured")
    else:
        st.sidebar.info("⚙️ Configure variables next")
    
    if st.session_state.label_config.get('barcode_variable'):
        st.sidebar.success(f"✅ Barcode: {st.session_state.label_config['barcode_variable']}")
    else:
        st.sidebar.info("📊 No barcode configured")
    
    # Navigation buttons
    st.sidebar.markdown("---")
    
    if st.sidebar.button("📤 Upload Data", use_container_width=True):
        st.session_state.current_page = 'upload'
        st.rerun()
        
    if st.sidebar.button("⚙️ Configure Labels", use_container_width=True):
        st.session_state.current_page = 'configure'
        st.rerun()
        
    if st.sidebar.button("🎨 Preview & Design", use_container_width=True):
        st.session_state.current_page = 'preview'
        st.rerun()
        
    if st.sidebar.button("🏭 Generate Labels", use_container_width=True):
        st.session_state.current_page = 'generate'
        st.rerun()
        
    if st.sidebar.button("📋 History", use_container_width=True):
        st.session_state.current_page = 'history'
        st.rerun()

def upload_data_page():
    """Handle file upload and data preview"""
    st.markdown('<div class="step-header"><h2>Step 1: Upload Your Excel Data</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Excel File")
        
        uploaded_file = st.file_uploader(
            "Choose your file",
            type=['xlsx', 'xls', 'csv'],
            help="Upload Excel or CSV file with your label data"
        )
        
        if uploaded_file is not None:
            try:
                # Read file based on extension
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Clean column names
                df.columns = df.columns.str.strip()
                
                # Store in session state
                st.session_state.uploaded_data = df
                
                st.success(f"✅ Successfully uploaded {len(df)} rows with {len(df.columns)} columns")
                
                # Show preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Show column info
                st.subheader("Available Columns")
                col_info = []
                for col in df.columns:
                    sample_values = df[col].dropna().head(2).tolist()
                    sample_text = ', '.join([str(v)[:25] for v in sample_values])
                    col_info.append({
                        'Column': col,
                        'Sample Data': sample_text
                    })
                
                st.dataframe(pd.DataFrame(col_info), use_container_width=True)
                
                st.info("✅ **Next:** Click 'Configure Labels' in the sidebar to set up your label variables.")
                
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    with col2:
        st.subheader("Sample Template")
        if st.button("📄 Download Sample"):
            sample_data = {
                'Product_Name': ['Widget A', 'Gadget B', 'Tool C'],
                'SKU': ['SKU001', 'SKU002', 'SKU003'],
                'Price': ['$29.99', '$45.50', '$12.75'],
                'Barcode_Value': ['123456789', '987654321', '456789123']
            }
            
            sample_df = pd.DataFrame(sample_data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                sample_df.to_excel(writer, sheet_name='Sample', index=False)
            
            st.download_button(
                "⬇️ Download Sample.xlsx",
                data=output.getvalue(),
                file_name="Sample_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def configure_labels_page():
    """Configure label variables and barcode settings"""
    st.markdown('<div class="step-header"><h2>Step 2: Configure Label Variables</h2></div>', unsafe_allow_html=True)
    
    if st.session_state.uploaded_data is None:
        st.warning("⚠️ Please upload your Excel data first!")
        st.info("👈 Click 'Upload Data' in the sidebar")
        return
    
    df = st.session_state.uploaded_data
    available_columns = list(df.columns)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Variable selection
        st.subheader("Select Variables for Labels")
        
        # Get current selection from session state
        current_selection = st.session_state.label_config.get('selected_variables', [])
        
        selected_vars = st.multiselect(
            "Choose which columns to include in your labels:",
            available_columns,
            default=current_selection,
            help="Select columns that should appear on your labels",
            key="variable_multiselect"
        )
        
        # Only update session state if selection actually changed
        if selected_vars != current_selection:
            st.session_state.label_config['selected_variables'] = selected_vars
            
            # Update variable order only when selection changes
            current_order = st.session_state.label_config.get('variable_order', [])
            
            # Add new variables to order
            for var in selected_vars:
                if var not in current_order:
                    current_order.append(var)
            
            # Remove variables no longer selected
            updated_order = [var for var in current_order if var in selected_vars]
            st.session_state.label_config['variable_order'] = updated_order
            
            # Force a rerun to sync the UI
            st.rerun()
        
        # Show current selection status
        if selected_vars:
            st.success(f"✅ Selected {len(selected_vars)} variables")
            
            # Configure each variable
            st.subheader("Variable Configuration")
            variable_order = st.session_state.label_config.get('variable_order', selected_vars)
            
            for i, var_name in enumerate(variable_order):
                if var_name in selected_vars:  # Only show if still selected
                    render_variable_config(var_name, i, df)
            
            # Barcode configuration
            st.subheader("Barcode Configuration")
            render_barcode_config(selected_vars)
        
        else:
            st.info("👆 Select at least one variable to configure your labels")
    
    with col2:
        # Label dimensions
        st.subheader("Label Dimensions")
        
        width = st.number_input(
            "Width (pixels)", 
            min_value=200, 
            max_value=800, 
            value=st.session_state.label_config['label_dimensions']['width']
        )
        
        height = st.number_input(
            "Height (pixels)", 
            min_value=100, 
            max_value=600, 
            value=st.session_state.label_config['label_dimensions']['height']
        )
        
        # Save dimensions
        st.session_state.label_config['label_dimensions'] = {
            'width': width, 
            'height': height
        }
        
        # Configuration summary
        if selected_vars:
            st.subheader("Current Configuration")
            st.write(f"**📏 Size:** {width} × {height} pixels")
            st.write(f"**📋 Variables:** {len(selected_vars)}")
            
            # Show variables in order
            for i, var in enumerate(st.session_state.label_config['variable_order']):
                settings = st.session_state.label_config['variable_settings'].get(var, {})
                font_size = settings.get('font_size', 12)
                st.write(f"  {i+1}. {var} ({font_size}px)")
            
            # Show barcode info
            barcode_var = st.session_state.label_config.get('barcode_variable', '')
            if barcode_var:
                st.write(f"**📊 Barcode:** {barcode_var}")
            else:
                st.write("**📊 Barcode:** Not configured")
            
            st.success("✅ Configuration saved!")
            st.info("👈 Click 'Preview & Design' to see your label")

def render_variable_config(var_name, index, df):
    """Render configuration for a single variable"""
    with st.container():
        st.markdown(f'<div class="variable-config">', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.2, 1.2, 1.1])
        
        # Move up/down buttons with better key management
        with col1:
            current_order = st.session_state.label_config.get('variable_order', [])
            
            if index > 0 and st.button("↑", key=f"up_{var_name}_{index}"):
                if var_name in current_order:
                    idx = current_order.index(var_name)
                    if idx > 0:
                        current_order[idx], current_order[idx-1] = current_order[idx-1], current_order[idx]
                        st.session_state.label_config['variable_order'] = current_order
                        st.rerun()
            
            if index < len(current_order) - 1 and st.button("↓", key=f"down_{var_name}_{index}"):
                if var_name in current_order:
                    idx = current_order.index(var_name)
                    if idx < len(current_order) - 1:
                        current_order[idx], current_order[idx+1] = current_order[idx+1], current_order[idx]
                        st.session_state.label_config['variable_order'] = current_order
                        st.rerun()
        
        # Variable name and sample
        with col2:
            st.write(f"**{var_name}**")
            if var_name in df.columns:
                sample_values = df[var_name].dropna().head(2).tolist()
                sample_text = ', '.join([str(v)[:15] for v in sample_values])
                st.caption(f"Sample: {sample_text}")
        
        # Font size with unique keys
        with col3:
            current_settings = st.session_state.label_config['variable_settings'].get(var_name, {})
            font_size = st.slider(
                "Font Size",
                min_value=8,
                max_value=24,
                value=current_settings.get('font_size', 12),
                key=f"font_{var_name}_{index}"
            )
        
        # Style with unique keys
        with col4:
            style = st.selectbox(
                "Style",
                ["Normal", "Bold"],
                index=0 if current_settings.get('style', 'Normal') == 'Normal' else 1,
                key=f"style_{var_name}_{index}"
            )
        
        # New Line option
        with col5:
            new_line = st.checkbox(
                "New Line",
                value=current_settings.get('new_line', True),
                key=f"newline_{var_name}_{index}",
                help="Uncheck to display on same line as previous variable"
            )
        
        # Save settings
        if var_name not in st.session_state.label_config['variable_settings']:
            st.session_state.label_config['variable_settings'][var_name] = {}
        
        st.session_state.label_config['variable_settings'][var_name].update({
            'font_size': font_size,
            'style': style,
            'new_line': new_line
        })
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_barcode_config(selected_vars):
    """Render barcode configuration section"""
    st.write("Choose which variable should be converted to a barcode:")
    
    # Current barcode variable
    current_barcode = st.session_state.label_config.get('barcode_variable', '')
    
    # Create radio options
    options = ['None'] + selected_vars
    
    # Find current index
    try:
        current_index = options.index(current_barcode) if current_barcode in options else 0
    except ValueError:
        current_index = 0
    
    # Radio button selection
    selected_barcode = st.radio(
        "Barcode Variable:",
        options,
        index=current_index,
        key="barcode_radio"
    )
    
    # Save selection immediately
    if selected_barcode == 'None':
        st.session_state.label_config['barcode_variable'] = ''
        st.info("💡 No barcode will be generated")
    else:
        st.session_state.label_config['barcode_variable'] = selected_barcode
        st.success(f"✅ Barcode variable: **{selected_barcode}**")
        
        # Barcode settings
        st.write("**Barcode Settings:**")
        col1, col2 = st.columns(2)
        
        # Get current settings
        current_settings = st.session_state.label_config.get('barcode_settings', {
            'height': 40,
            'show_text': False,
            'font_size': 10
        })
        
        with col1:
            height = st.slider(
                "Barcode Height",
                min_value=30,
                max_value=80,
                value=current_settings.get('height', 40),
                key="barcode_height_slider"
            )
        
        with col2:
            show_text = st.checkbox(
                "Show text below barcode",
                value=current_settings.get('show_text', False),
                key="barcode_show_text_check"
            )
        
        # Save barcode settings immediately
        st.session_state.label_config['barcode_settings'] = {
            'height': height,
            'show_text': show_text,
            'font_size': current_settings.get('font_size', 10)
        }
        
        # Show current state for verification
        if show_text:
            st.info(f"💡 '{selected_barcode}' will appear as barcode with text below")
        else:
            st.info(f"💡 '{selected_barcode}' will appear as barcode only (no text)")
    
    # Debug verification
    with st.expander("🔧 Debug - Barcode Settings"):
        current_settings = st.session_state.label_config.get('barcode_settings', {})
        st.write(f"**Barcode Variable:** {st.session_state.label_config.get('barcode_variable', 'NOT SET')}")
        st.write(f"**Show Text Setting:** {current_settings.get('show_text', 'NOT SET')}")
        st.write(f"**Height Setting:** {current_settings.get('height', 'NOT SET')}")
        
        if selected_barcode != 'None':
            if current_settings.get('show_text') == show_text:
                st.success("✅ Settings match correctly")
            else:
                st.error("❌ Settings mismatch detected!")
                if st.button("🔄 Force Sync Settings"):
                    st.session_state.label_config['barcode_settings']['show_text'] = show_text
                    st.rerun()

def preview_design_page():
    """Preview label design with real data"""
    st.markdown('<div class="step-header"><h2>Step 3: Preview & Design</h2></div>', unsafe_allow_html=True)
    
    if st.session_state.uploaded_data is None:
        st.warning("⚠️ Please upload your Excel data first!")
        return
    
    if not st.session_state.label_config['selected_variables']:
        st.warning("⚠️ Please configure your label variables first!")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Live Preview")
        
        try:
            preview_image = create_preview_label()
            st.image(preview_image, caption="Preview with Real Data", use_column_width=True)
            
            # Show barcode status
            barcode_var = st.session_state.label_config.get('barcode_variable', '')
            if barcode_var:
                st.success(f"✅ Barcode: {barcode_var}")
                if BARCODE_AVAILABLE:
                    st.info("🟢 Real barcode generation available")
                else:
                    st.warning("🟡 Install 'python-barcode' for real barcodes")
            else:
                st.info("ℹ️ No barcode configured")
            
            # Show first row data
            df = st.session_state.uploaded_data
            first_row = df.iloc[0]
            
            st.subheader("Data from Row 1")
            preview_data = {}
            for var in st.session_state.label_config['selected_variables']:
                if var in first_row:
                    preview_data[var] = first_row[var]
            
            for key, value in preview_data.items():
                st.write(f"**{key}:** {value}")
                
        except Exception as e:
            st.error(f"Error generating preview: {str(e)}")
    
    with col2:
        st.subheader("Configuration Summary")
        
        config = st.session_state.label_config
        st.write(f"**📏 Dimensions:** {config['label_dimensions']['width']} × {config['label_dimensions']['height']}px")
        st.write(f"**📋 Variables:** {len(config['selected_variables'])}")
        
        # Show variable order
        st.write("**Variable Order:**")
        for i, var in enumerate(config['variable_order']):
            settings = config['variable_settings'].get(var, {})
            font_size = settings.get('font_size', 12)
            style = settings.get('style', 'Normal')
            
            if var == config.get('barcode_variable'):
                st.write(f"  {i+1}. **{var}** (Barcode)")
            else:
                st.write(f"  {i+1}. {var} ({font_size}px, {style})")
        
        # Global adjustments
        st.subheader("Quick Adjustments")
        
        col_up, col_down = st.columns(2)
        with col_up:
            if st.button("📈 Increase All Fonts"):
                for var in config['selected_variables']:
                    if var not in config['variable_settings']:
                        config['variable_settings'][var] = {}
                    current = config['variable_settings'][var].get('font_size', 12)
                    config['variable_settings'][var]['font_size'] = min(24, current + 2)
                st.rerun()
        
        with col_down:
            if st.button("📉 Decrease All Fonts"):
                for var in config['selected_variables']:
                    if var not in config['variable_settings']:
                        config['variable_settings'][var] = {}
                    current = config['variable_settings'][var].get('font_size', 12)
                    config['variable_settings'][var]['font_size'] = max(8, current - 2)
                st.rerun()

def create_preview_label():
    """Create preview label with real data from first row"""
    config = st.session_state.label_config
    width = config['label_dimensions']['width']
    height = config['label_dimensions']['height']
    
    df = st.session_state.uploaded_data
    if df is None or len(df) == 0:
        return create_empty_label()
    
    first_row = df.iloc[0]
    
    # Use the same logic as production labels
    return create_label_from_data(first_row)

def add_barcode_to_image(img, draw, barcode_data, width, height, config):
    """Add barcode to the label image (used for preview)"""
    barcode_settings = config.get('barcode_settings', {})
    barcode_height = barcode_settings.get('height', 40)
    barcode_str = str(barcode_data)
    
    # Position at bottom with more space
    barcode_y = height - barcode_height - 15
    barcode_width = width - 20
    
    if BARCODE_AVAILABLE:
        try:
            # Generate real barcode with higher DPI
            code128 = barcode.get('code128', barcode_str, writer=ImageWriter())
            
            # Create barcode image with high quality
            barcode_buffer = io.BytesIO()
            # Write with options for better quality
            barcode_img_raw = code128.render({
                'module_width': 0.4,  # Thinner bars for better quality
                'module_height': barcode_height,
                'background': 'white',
                'foreground': 'black',
                'write_text': False,  # Don't include text in barcode image
                'text_distance': 0,
                'quiet_zone': 2
            })
            
            # Save as high quality
            barcode_img_raw.save(barcode_buffer, format='PNG', dpi=(300, 300))
            barcode_buffer.seek(0)
            
            barcode_img = Image.open(barcode_buffer)
            barcode_img = barcode_img.resize((barcode_width, barcode_height), Image.Resampling.LANCZOS)
            
            # Paste onto main image
            img.paste(barcode_img, (10, barcode_y))
            
        except Exception:
            # Fallback to visual barcode
            draw_visual_barcode(draw, 10, barcode_y, barcode_width, barcode_height, barcode_str)
    else:
        # Draw visual barcode
        draw_visual_barcode(draw, 10, barcode_y, barcode_width, barcode_height, barcode_str)
    
    # Add text below if explicitly enabled
    if barcode_settings.get('show_text', False):
        font = load_font(barcode_settings.get('font_size', 10))
        if font:
            draw.text((15, barcode_y + barcode_height + 3), barcode_str, fill='black', font=font)

def draw_visual_barcode(draw, x, y, width, height, data):
    """Draw visual representation of barcode"""
    # Background
    draw.rectangle([x, y, x + width, y + height], fill='white', outline='black', width=2)
    
    # Generate bars based on data
    data_str = str(data)
    bar_count = min(len(data_str) * 4, 50)
    bar_width = max(2, (width - 20) // bar_count)
    
    for i in range(bar_count):
        char_idx = i % len(data_str)
        char_code = ord(data_str[char_idx])
        
        # Vary bar heights
        if char_code % 4 == 0:
            bar_height = height - 8
        elif char_code % 3 == 0:
            bar_height = height - 12
        else:
            bar_height = height - 6
        
        x_pos = x + 10 + (i * bar_width)
        
        # Draw bars with pattern
        if (char_code + i) % 3 != 0:
            draw.rectangle([x_pos, y + 4, x_pos + bar_width - 1, y + 4 + bar_height], fill='black')

def load_font(size):
    """Load font with fallback - alias for compatibility"""
    return load_high_quality_font(size)

def create_empty_label():
    """Create empty label placeholder"""
    config = st.session_state.label_config
    width = config['label_dimensions']['width']
    height = config['label_dimensions']['height']
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, width-2, height-2], outline='black', width=2)
    
    font = load_font(16)
    if font:
        draw.text((width//2 - 50, height//2), "No data", fill='gray', font=font)
    
    return img

def generate_labels_page():
    """Generate final labels"""
    st.markdown('<div class="step-header"><h2>Step 4: Generate Labels</h2></div>', unsafe_allow_html=True)
    
    if st.session_state.uploaded_data is None:
        st.warning("⚠️ Upload data first!")
        return
    
    if not st.session_state.label_config['selected_variables']:
        st.warning("⚠️ Configure variables first!")
        return
    
    df = st.session_state.uploaded_data
    
    st.write(f"**Ready to generate {len(df)} labels**")
    
    # Range selection
    use_all = st.checkbox("Generate all labels", value=True)
    
    if not use_all:
        col1, col2 = st.columns(2)
        with col1:
            start = st.number_input("Start row", 1, len(df), 1) - 1
        with col2:
            end = st.number_input("End row", 1, len(df), min(100, len(df)))
        
        selected_df = df.iloc[start:end]
    else:
        selected_df = df
    
    st.write(f"Will generate **{len(selected_df)}** labels")
    
    # Generate button
    if st.button("🏭 Generate PNG Labels", type="primary", use_container_width=True):
        with st.spinner(f"Generating {len(selected_df)} labels..."):
            try:
                zip_data = generate_png_labels(selected_df)
                filename = f"Labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                
                st.success(f"✅ Generated {len(selected_df)} labels!")
                
                st.download_button(
                    "⬇️ Download ZIP",
                    data=zip_data,
                    file_name=filename,
                    mime="application/zip",
                    use_container_width=True
                )
                
                # Save to history
                st.session_state.generated_labels.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'count': len(selected_df),
                    'format': 'PNG'
                })
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def generate_png_labels(df):
    """Generate PNG labels and return ZIP"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for index, row in df.iterrows():
            try:
                # Create label image
                label_img = create_label_from_data(row)
                
                # Save to buffer
                img_buffer = io.BytesIO()
                label_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Add to ZIP
                filename = f"label_{index + 1:04d}.png"
                zip_file.writestr(filename, img_buffer.getvalue())
                
            except Exception as e:
                st.warning(f"Skipped label {index + 1}: {str(e)}")
                continue
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def create_label_from_data(row_data):
    """Create high-quality label image from row data"""
    config = st.session_state.label_config
    width = config['label_dimensions']['width']
    height = config['label_dimensions']['height']
    
    # Create even higher resolution image for maximum clarity
    scale_factor = 4  # Increased from 3x to 4x for better clarity
    high_width = width * scale_factor
    high_height = height * scale_factor
    
    # Create high-res image
    img = Image.new('RGB', (high_width, high_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw border (scaled)
    border_width = 3 * scale_factor  # Thicker border for better definition
    draw.rectangle([border_width, border_width, high_width-border_width, high_height-border_width], 
                   outline='black', width=border_width)
    
    y_offset = 20 * scale_factor  # More top margin
    barcode_variable = config.get('barcode_variable', '')
    
    # Calculate available height for text (reserve space for barcode)
    barcode_height = config['barcode_settings']['height'] * scale_factor
    available_height = high_height - barcode_height - (60 * scale_factor)  # More space reserved
    
    # Group variables into lines based on new_line setting
    text_lines = []
    current_line = []
    
    for var in config['variable_order']:
        if var in config['selected_variables'] and var != barcode_variable:
            if var in row_data and pd.notna(row_data[var]):
                settings = config['variable_settings'].get(var, {})
                font_size = settings.get('font_size', 12) * scale_factor
                new_line = settings.get('new_line', True)
                
                # Load high-quality font
                font = load_high_quality_font(font_size)
                if font is None:
                    continue
                
                # Create text with better formatting
                value = str(row_data[var])
                text = f"{var}: {value}"
                
                # If this variable should start a new line, save current line and start new
                if new_line and current_line:
                    text_lines.append(current_line)
                    current_line = []
                
                current_line.append({
                    'text': text,
                    'font': font,
                    'font_size': font_size,
                    'var_name': var,
                    'value': value
                })
                
                # If this variable should start a new line, close the current line
                if new_line:
                    text_lines.append(current_line)
                    current_line = []
    
    # Add any remaining variables in current_line
    if current_line:
        text_lines.append(current_line)
    
    # Process each line and fit text
    processed_lines = []
    for line in text_lines:
        if not line:
            continue
            
        # If single item on line, handle normally
        if len(line) == 1:
            item = line[0]
            text = item['text']
            font = item['font']
            font_size = item['font_size']
            
            # Smart truncation for single items
            text_width = draw.textlength(text, font=font)
            max_width = high_width - (40 * scale_factor)
            
            if text_width > max_width:
                # Abbreviate variable names
                short_var = item['var_name'].replace('_', ' ').replace('Manufacturer', 'Mfg').replace('Product', 'Prod')
                text = f"{short_var}: {item['value']}"
                text_width = draw.textlength(text, font=font)
                
                if text_width > max_width:
                    avg_char_width = text_width / len(text)
                    max_chars = int(max_width / avg_char_width) - 3
                    
                    if len(text) > max_chars:
                        if ',' in item['value'] and len(f"{short_var}: {item['value'].split(',')[0]}...") <= max_chars:
                            text = f"{short_var}: {item['value'].split(',')[0]}..."
                        else:
                            text = text[:max_chars] + "..."
            
            processed_lines.append([(text, font, font_size)])
            
        else:
            # Multiple items on same line - create compact format
            line_items = []
            for item in line:
                # Use shorter format for inline items
                short_var = item['var_name'].replace('_', ' ').replace('Manufacturer', 'Mfg').replace('Product', 'Prod')
                compact_text = f"{short_var}: {item['value']}"
                line_items.append((compact_text, item['font'], item['font_size']))
            
            # Join with separator and check if fits
            separator = "  |  "
            combined_text = separator.join([item[0] for item in line_items])
            
            # Use the largest font size in the line
            max_font_size = max(item[2] for item in line_items)
            max_font = load_high_quality_font(max_font_size)
            
            if max_font:
                text_width = draw.textlength(combined_text, font=max_font)
                max_width = high_width - (40 * scale_factor)
                
                if text_width > max_width:
                    # If too long, truncate values
                    truncated_items = []
                    for compact_text, font, font_size in line_items:
                        if ':' in compact_text:
                            var_part, val_part = compact_text.split(':', 1)
                            val_part = val_part.strip()
                            if len(val_part) > 8:
                                val_part = val_part[:8] + "..."
                            truncated_items.append((f"{var_part}: {val_part}", font, font_size))
                        else:
                            truncated_items.append((compact_text, font, font_size))
                    
                    combined_text = separator.join([item[0] for item in truncated_items])
                
                processed_lines.append([(combined_text, max_font, max_font_size)])
    
    # Center all lines vertically
    total_height = sum(max(item[2] for item in line) + (8 * scale_factor) for line in processed_lines)
    start_y = (available_height - total_height) // 2 + (30 * scale_factor)
    
    # Draw all lines
    current_y = start_y
    for line in processed_lines:
        for text, font, font_size in line:
            # Center horizontally
            text_width = draw.textlength(text, font=font)
            x_pos = (high_width - text_width) // 2
            
            draw.text((x_pos, current_y), text, fill='black', font=font)
            break  # Only one item per processed line
        
        max_font_size = max(item[2] for item in line)
        current_y += max_font_size + (8 * scale_factor)
    
    # Add barcode if configured (centered)
    if barcode_variable and barcode_variable in row_data and pd.notna(row_data[barcode_variable]):
        add_high_quality_barcode(img, draw, row_data[barcode_variable], high_width, high_height, config, scale_factor)
    
    # Scale down to final size with highest quality resampling
    final_img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    return final_img

def add_high_quality_barcode(img, draw, barcode_data, width, height, config, scale_factor):
    """Add high-quality centered barcode to scaled image"""
    barcode_settings = config.get('barcode_settings', {})
    barcode_height = barcode_settings.get('height', 40) * scale_factor
    barcode_str = str(barcode_data)
    
    # Position at bottom with proper spacing
    barcode_y = height - barcode_height - (20 * scale_factor)
    barcode_width = width - (40 * scale_factor)  # More side margins
    
    if BARCODE_AVAILABLE:
        try:
            # Generate ultra-high-quality barcode
            code128 = barcode.get('code128', barcode_str, writer=ImageWriter())
            
            # Create barcode with maximum quality settings
            barcode_buffer = io.BytesIO()
            barcode_img_raw = code128.render({
                'module_width': 0.25,  # Even thinner bars for crisp quality
                'module_height': barcode_height // scale_factor,
                'background': 'white',
                'foreground': 'black',
                'write_text': False,  # Never include text
                'text_distance': 0,
                'quiet_zone': 4,  # More quiet zone for better scanning
                'dpi': 600  # Very high DPI
            })
            
            # Save with maximum quality
            barcode_img_raw.save(barcode_buffer, format='PNG', dpi=(600, 600))
            barcode_buffer.seek(0)
            
            barcode_img = Image.open(barcode_buffer)
            # Scale the barcode for high-res image
            barcode_img = barcode_img.resize((barcode_width, barcode_height), Image.Resampling.LANCZOS)
            
            # Center the barcode horizontally
            barcode_x = (width - barcode_width) // 2
            
            # Paste onto main image
            img.paste(barcode_img, (barcode_x, barcode_y))
            
        except Exception:
            # Fallback to visual barcode (centered)
            barcode_x = (width - barcode_width) // 2
            draw_visual_barcode_scaled(draw, barcode_x, barcode_y, barcode_width, barcode_height, barcode_str)
    else:
        # Draw visual barcode (centered)
        barcode_x = (width - barcode_width) // 2
        draw_visual_barcode_scaled(draw, barcode_x, barcode_y, barcode_width, barcode_height, barcode_str)
    
    # Add text below if explicitly enabled
    if barcode_settings.get('show_text', False):
        font = load_high_quality_font(barcode_settings.get('font_size', 10) * scale_factor)
        if font:
            # Center the text below barcode
            text_width = draw.textlength(barcode_str, font=font)
            text_x = (width - text_width) // 2
            text_y = barcode_y + barcode_height + (5 * scale_factor)
            
            draw.text((text_x, text_y), barcode_str, fill='black', font=font)

def draw_visual_barcode_scaled(draw, x, y, width, height, data):
    """Draw high-quality visual barcode for scaled image"""
    # Background
    draw.rectangle([x, y, x + width, y + height], fill='white', outline='black', width=3)
    
    # Generate bars
    data_str = str(data)
    bar_count = min(len(data_str) * 4, 60)
    bar_width = max(3, (width - 30) // bar_count)
    
    for i in range(bar_count):
        char_idx = i % len(data_str)
        char_code = ord(data_str[char_idx])
        
        # Vary bar heights
        if char_code % 4 == 0:
            bar_height = height - 12
        elif char_code % 3 == 0:
            bar_height = height - 18
        else:
            bar_height = height - 9
        
        x_pos = x + 15 + (i * bar_width)
        
        # Draw bars with pattern
        if (char_code + i) % 3 != 0:
            draw.rectangle([x_pos, y + 6, x_pos + bar_width - 1, y + 6 + bar_height], fill='black')

def load_high_quality_font(size):
    """Load high-quality font with multiple fallbacks"""
    font_names = [
        "arial.ttf",
        "Arial.ttf", 
        "helvetica.ttf",
        "Helvetica.ttf",
        "DejaVuSans.ttf",
        "liberation-sans.ttf"
    ]
    
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except:
            continue
    
    # Final fallback
    try:
        return ImageFont.load_default()
    except:
        return None
    for var in config['variable_order']:
        if var in config['selected_variables'] and var != barcode_variable:
            if var in row_data and pd.notna(row_data[var]):
                settings = config['variable_settings'].get(var, {})
                font_size = settings.get('font_size', 12)
                
                # Load font
                font = load_font(font_size)
                if font is None:
                    continue
                
                # Create text
                text = f"{var}: {row_data[var]}"
                if len(text) > 45:
                    text = text[:42] + "..."
                
                draw.text((10, y_offset), text, fill='black', font=font)
                y_offset += font_size + 6
    
    # Add barcode if configured
    if barcode_variable and barcode_variable in row_data and pd.notna(row_data[barcode_variable]):
        add_barcode_to_image(img, draw, row_data[barcode_variable], width, height, config)
    
    return img

def history_page():
    """Show generation history"""
    st.markdown('<div class="step-header"><h2>Label Generation History</h2></div>', unsafe_allow_html=True)
    
    if st.session_state.generated_labels:
        st.subheader("Recent Generations")
        
        for i, gen in enumerate(st.session_state.generated_labels):
            st.write(f"**{i+1}.** {gen['timestamp']} - {gen['count']} labels ({gen['format']})")
        
        if st.button("🗑️ Clear History"):
            st.session_state.generated_labels = []
            st.rerun()
    else:
        st.info("No labels generated yet")
        st.write("**Steps to generate labels:**")
        st.write("1. Upload Excel file")
        st.write("2. Configure variables")
        st.write("3. Preview design")
        st.write("4. Generate labels")

# Initialize current page if not set
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'upload'

# Run the application
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.write("Please refresh the page")