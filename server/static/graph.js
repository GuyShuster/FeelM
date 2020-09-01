$(document).ready(function() {
    $(chart_id).highcharts({
        title: title,
        yAxis: yAxis,
        xAxis: xAxis,
        chart: chart,
        series: series,
    });
});