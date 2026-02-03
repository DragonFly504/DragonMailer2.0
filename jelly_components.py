"""
Jelly Slider Components for Streamlit
Based on: https://github.com/popwarsweet/JellySlider
Adapted for web using CSS/SVG animations
"""

import streamlit as st


def _get_track_colors(color: str) -> dict:
    """Generate track colors based on accent color, adapting to light/dark."""
    # Detect if color is light or dark based on hex
    # For now, use darker track for all (works better with glow effects)
    return {
        "track_bg": "linear-gradient(180deg, #2a2a2a 0%, #3d3d3d 50%, #2a2a2a 100%)",
        "track_shadow": "rgba(0, 0, 0, 0.6)",
        "fill_start": "#4a4a4a",
        "fill_mid": "#5a5a5a",
        "text_on_fill": "#1a1a1a"
    }


def jelly_progress(value: float, label: str = "", color: str = "#c8ff00"):
    """
    Display a jelly-style animated progress bar.
    
    Args:
        value: Progress value (0.0 to 1.0)
        label: Optional label text
        color: Primary color (default: neon green/yellow)
    """
    percentage = int(value * 100)
    track = _get_track_colors(color)
    
    # Calculate glow intensity based on progress
    glow_intensity = 0.3 + (value * 0.5)
    
    html = f"""
    <style>
        @keyframes jellyPulse {{
            0%, 100% {{ 
                filter: drop-shadow(0 0 8px {color}80);
                transform: scaleY(1);
            }}
            50% {{ 
                filter: drop-shadow(0 0 20px {color}cc);
                transform: scaleY(1.02);
            }}
        }}
        
        @keyframes jellyBounce {{
            0% {{ transform: translateX(0) scaleX(1); }}
            25% {{ transform: translateX(2px) scaleX(0.98); }}
            50% {{ transform: translateX(0) scaleX(1.02); }}
            75% {{ transform: translateX(-2px) scaleX(0.98); }}
            100% {{ transform: translateX(0) scaleX(1); }}
        }}
        
        @keyframes glowPulse {{
            0%, 100% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
        }}
        
        .jelly-container {{
            width: 100%;
            padding: 20px 0;
            position: relative;
        }}
        
        .jelly-label {{
            color: {color};
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
            text-shadow: 0 0 10px {color}80;
        }}
        
        .jelly-track {{
            width: 100%;
            height: 24px;
            background: linear-gradient(180deg, #2a2a2a 0%, #3d3d3d 50%, #2a2a2a 100%);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            box-shadow: 
                inset 0 2px 8px {track["track_shadow"]},
                inset 0 -1px 2px rgba(255, 255, 255, 0.05),
                0 1px 3px rgba(0, 0, 0, 0.3);
        }}
        
        .jelly-fill {{
            width: {percentage}%;
            height: 100%;
            background: linear-gradient(90deg, 
                {track["fill_start"]} 0%, 
                {track["fill_mid"]} 20%,
                {color}88 60%, 
                {color} 85%,
                {color}ee 100%
            );
            border-radius: 12px;
            position: relative;
            animation: jellyPulse 2s ease-in-out infinite;
            transition: width 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }}
        
        .jelly-fill::before {{
            content: '';
            position: absolute;
            top: 2px;
            left: 10px;
            right: 10px;
            height: 6px;
            background: linear-gradient(180deg, 
                rgba(255, 255, 255, 0.3) 0%, 
                rgba(255, 255, 255, 0.05) 100%
            );
            border-radius: 3px;
        }}
        
        .jelly-fill::after {{
            content: '';
            position: absolute;
            right: 5px;
            top: 50%;
            transform: translateY(-50%);
            width: 16px;
            height: 16px;
            background: radial-gradient(circle, {color} 0%, {color}00 70%);
            border-radius: 50%;
            animation: glowPulse 1.5s ease-in-out infinite;
        }}
        
        .jelly-bubble {{
            position: absolute;
            right: calc({100 - percentage}% - 16px);
            top: -8px;
            width: 40px;
            height: 40px;
            background: radial-gradient(circle at 30% 30%, 
                {color}ff 0%, 
                {color}cc 40%, 
                {color}88 70%,
                {color}44 100%
            );
            border-radius: 50%;
            box-shadow: 
                0 0 20px {color}80,
                0 0 40px {color}40,
                inset 0 -5px 15px {color}88;
            animation: jellyBounce 3s ease-in-out infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
            color: {track["text_on_fill"]};
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
        }}
        
        .jelly-percentage {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: {track["text_on_fill"]};
            font-size: 12px;
            font-weight: 700;
            text-shadow: 0 0 5px {color};
            z-index: 10;
        }}
        
        .jelly-particles {{
            position: absolute;
            right: calc({100 - percentage}%);
            top: 0;
            width: 30px;
            height: 100%;
            pointer-events: none;
        }}
        
        .particle {{
            position: absolute;
            width: 4px;
            height: 4px;
            background: {color};
            border-radius: 50%;
            animation: particleFade 1s ease-out infinite;
        }}
        
        @keyframes particleFade {{
            0% {{ opacity: 1; transform: translateY(0) scale(1); }}
            100% {{ opacity: 0; transform: translateY(-20px) scale(0); }}
        }}
    </style>
    
    <div class="jelly-container">
        {"<div class='jelly-label'>" + label + "</div>" if label else ""}
        <div class="jelly-track">
            <div class="jelly-fill">
                <span class="jelly-percentage">{percentage}%</span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def jelly_slider_display(value: float, min_val: float = 0, max_val: float = 100, 
                         label: str = "", color: str = "#c8ff00"):
    """
    Display a jelly-style slider (display only, use with st.slider for input).
    
    Args:
        value: Current value
        min_val: Minimum value
        max_val: Maximum value
        label: Label text
        color: Primary color
    """
    normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
    
    html = f"""
    <style>
        @keyframes bubbleFloat {{
            0%, 100% {{ transform: translateY(0) scale(1); }}
            50% {{ transform: translateY(-5px) scale(1.05); }}
        }}
        
        @keyframes trackGlow {{
            0%, 100% {{ box-shadow: 0 0 10px {color}40; }}
            50% {{ box-shadow: 0 0 25px {color}80; }}
        }}
        
        .slider-container {{
            width: 100%;
            padding: 30px 20px 20px 20px;
            position: relative;
        }}
        
        .slider-label {{
            color: {color};
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
        }}
        
        .slider-value {{
            font-size: 24px;
            text-shadow: 0 0 15px {color};
        }}
        
        .slider-track {{
            width: 100%;
            height: 14px;
            background: linear-gradient(180deg, #252525 0%, #3a3a3a 50%, #252525 100%);
            border-radius: 7px;
            position: relative;
            box-shadow: 
                inset 0 2px 6px rgba(0, 0, 0, 0.5),
                0 1px 2px rgba(255, 255, 255, 0.05);
            animation: trackGlow 3s ease-in-out infinite;
        }}
        
        .slider-fill {{
            width: {normalized * 100}%;
            height: 100%;
            background: linear-gradient(90deg, 
                #3a3a3a 0%,
                #555 30%,
                {color}99 70%,
                {color} 100%
            );
            border-radius: 7px;
            position: relative;
            transition: width 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}
        
        .slider-fill::before {{
            content: '';
            position: absolute;
            top: 2px;
            left: 5px;
            right: 5px;
            height: 4px;
            background: linear-gradient(180deg, 
                rgba(255, 255, 255, 0.25) 0%, 
                transparent 100%
            );
            border-radius: 2px;
        }}
        
        .slider-knob {{
            position: absolute;
            left: calc({normalized * 100}% - 18px);
            top: -11px;
            width: 36px;
            height: 36px;
            background: radial-gradient(circle at 35% 35%,
                #ffffff 0%,
                {color} 30%,
                {color}cc 60%,
                {color}88 100%
            );
            border-radius: 50%;
            box-shadow: 
                0 0 20px {color},
                0 0 40px {color}66,
                0 4px 8px rgba(0, 0, 0, 0.3),
                inset 0 2px 4px rgba(255, 255, 255, 0.4);
            animation: bubbleFloat 2s ease-in-out infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: left 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}
        
        .slider-knob-inner {{
            width: 12px;
            height: 12px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 50%;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4);
        }}
    </style>
    
    <div class="slider-container">
        <div class="slider-label">
            <span>{label}</span>
            <span class="slider-value">{value:.1f}</span>
        </div>
        <div class="slider-track">
            <div class="slider-fill"></div>
            <div class="slider-knob">
                <div class="slider-knob-inner"></div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def jelly_loading(text: str = "Loading...", color: str = "#c8ff00"):
    """
    Display a jelly-style loading animation.
    
    Args:
        text: Loading text
        color: Primary color
    """
    html = f"""
    <style>
        @keyframes jellyWave {{
            0%, 100% {{ transform: scaleY(0.5); }}
            50% {{ transform: scaleY(1.5); }}
        }}
        
        .loading-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }}
        
        .loading-bars {{
            display: flex;
            gap: 6px;
            margin-bottom: 15px;
        }}
        
        .loading-bar {{
            width: 8px;
            height: 40px;
            background: linear-gradient(180deg, {color} 0%, {color}66 100%);
            border-radius: 4px;
            box-shadow: 0 0 15px {color}80;
        }}
        
        .loading-bar:nth-child(1) {{ animation: jellyWave 0.8s ease-in-out 0s infinite; }}
        .loading-bar:nth-child(2) {{ animation: jellyWave 0.8s ease-in-out 0.1s infinite; }}
        .loading-bar:nth-child(3) {{ animation: jellyWave 0.8s ease-in-out 0.2s infinite; }}
        .loading-bar:nth-child(4) {{ animation: jellyWave 0.8s ease-in-out 0.3s infinite; }}
        .loading-bar:nth-child(5) {{ animation: jellyWave 0.8s ease-in-out 0.4s infinite; }}
        
        .loading-text {{
            color: {color};
            font-size: 14px;
            font-weight: 600;
            text-shadow: 0 0 10px {color}80;
        }}
    </style>
    
    <div class="loading-container">
        <div class="loading-bars">
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
        </div>
        <div class="loading-text">{text}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def jelly_metric(label: str, value: str, delta: str = None, color: str = "#c8ff00"):
    """
    Display a jelly-style metric card.
    
    Args:
        label: Metric label
        value: Main value
        delta: Optional delta/change value
        color: Primary color
    """
    delta_html = ""
    if delta:
        is_positive = not delta.startswith("-")
        delta_color = "#00ff88" if is_positive else "#ff4466"
        arrow = "↑" if is_positive else "↓"
        delta_html = f'<div class="metric-delta" style="color: {delta_color};">{arrow} {delta}</div>'
    
    html = f"""
    <style>
        @keyframes metricGlow {{
            0%, 100% {{ box-shadow: 0 0 15px {color}30, inset 0 0 30px {color}10; }}
            50% {{ box-shadow: 0 0 25px {color}50, inset 0 0 40px {color}20; }}
        }}
        
        .metric-card {{
            background: linear-gradient(145deg, #1a1a1a 0%, #252525 50%, #1a1a1a 100%);
            border: 1px solid {color}44;
            border-radius: 16px;
            padding: 20px;
            animation: metricGlow 3s ease-in-out infinite;
            margin: 10px 0;
        }}
        
        .metric-label {{
            color: {color}cc;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            color: {color};
            font-size: 36px;
            font-weight: 700;
            text-shadow: 0 0 20px {color}80;
            margin-bottom: 5px;
        }}
        
        .metric-delta {{
            font-size: 14px;
            font-weight: 600;
        }}
    </style>
    
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# Example usage and demo
if __name__ == "__main__":
    st.set_page_config(page_title="Jelly Components Demo", layout="wide")
    
    st.markdown("""
        <style>
            .stApp { background: #0a0a0a; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🟢 Jelly Components Demo")
    
    # Progress bars
    st.subheader("Progress Bars")
    jelly_progress(0.75, "Download Progress")
    jelly_progress(0.45, "Upload Progress", "#00ff88")
    jelly_progress(0.90, "Processing", "#ff6b35")
    
    # Slider display
    st.subheader("Slider Display")
    val = st.slider("Value", 0, 100, 65)
    jelly_slider_display(val, 0, 100, "Volume")
    
    # Loading
    st.subheader("Loading Animation")
    jelly_loading("Processing emails...")
    
    # Metrics
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        jelly_metric("Emails Sent", "1,234", "+56")
    with col2:
        jelly_metric("Success Rate", "98.5%", "+2.3%")
    with col3:
        jelly_metric("Failed", "18", "-5")
