if (document.readyState !== 'loading') {
    init_chart();
} else {
    document.addEventListener('DOMContentLoaded', init_chart);
}

function init_chart() {
    const configScript = document.getElementById("adminchart-chartjs-config");
    if (!configScript) return;
    const chartConfig = JSON.parse(configScript.textContent);
    if (!chartConfig) return;
    var container = document.getElementById('admincharts')
    var canvas = document.createElement("canvas")
    container.appendChild(canvas)
    var ctx = canvas.getContext('2d');
    const style = getComputedStyle(document.documentElement)
    const fg_color = style.getPropertyValue('--body-fg');
    const bg_color = style.getPropertyValue('--hairline-color');
    Chart.defaults.borderColor = bg_color;
    Chart.defaults.color = fg_color;
    var chart = new Chart(ctx, chartConfig);

}
