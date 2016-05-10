
/*
NAME
    changeGraphData - Fetch graph data for some tracker
Synopsis
    changeGraphData(elem)
        elem        -> the html element of the drop-down input
DESCRIPTION
    Fetches graph data for a tracker and replaces the content of the graph with the new data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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
