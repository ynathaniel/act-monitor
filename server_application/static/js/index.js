function changeGraphData(elem) {
    var object_name = $(elem).val()
    var graph_data_url = "/api/dashboard/graph?object_name=" + object_name
    $.get(graph_data_url, function(graph_data) {
        if (graph_data) {
            line_data.labels = graph_data.labels
            line_data.datasets[0].data = graph_data.values

            LineChart.destroy()
            LineChart = new Chart(graphChart).Line(line_data, graph_options);
        }
    })
}
