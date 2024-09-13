// question_map.js

document.addEventListener('DOMContentLoaded', function () {
    // Harita verilerini global bir değişkende tutalım
    var questionNodes = JSON.parse(document.getElementById('question-nodes-data').textContent);
    var allNodes = questionNodes.nodes;
    var allLinks = questionNodes.links;

    function createChart(nodes, links) {
        d3.select("#chart").html("");

        var width = document.getElementById('chart').clientWidth;
        var height = 800;

        var zoom = d3.zoom()
            .scaleExtent([0.5, 5])
            .on("zoom", function(event) {
                svg.attr("transform", event.transform);
            });

        var svg = d3.select("#chart")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(zoom)
            .append("g");

        var defs = svg.append("defs");

        defs.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "-0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("xoverflow", "visible")
            .append("svg:path")
            .attr("d", "M 0,-5 L 10 ,0 L 0,5")
            .attr("fill", "#999")
            .style("stroke", "none");

        var simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links)
                .id(function(d) { return d.id; })
                .distance(200) // Mesafeyi artırdık
            )
            .force("charge", d3.forceManyBody().strength(-500)) // İtme kuvvetini artırdık
            .force("center", d3.forceCenter(width / 2, height / 2));

        var link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke-width", 2)
            .attr("stroke", "#999")
            .attr("marker-end", "url(#arrowhead)");

        var node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("r", function(d) { return d.size; })
            .attr("fill", function(d) { return d.color; })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("click", function(event, d) {
                window.location.href = "/question/" + d.id.replace("q", "");
            });

        var label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .attr("dy", -25)
            .attr("text-anchor", "middle")
            .text(function(d) { return d.label; });

        simulation.on("tick", function() {
            link
                .attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node
                .attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });

            label
                .attr("x", function(d) { return d.x; })
                .attr("y", function(d) { return d.y - 10; });
        });

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }

    // Başlangıçta tüm verilerle haritayı oluştur
    createChart(allNodes, allLinks);

    // Filtreleme butonlarının etkinliklerini tanımla
    document.getElementById('btn-me').addEventListener('click', function() {
        fetch('/map-data/?filter=me')
            .then(response => response.json())
            .then(data => {
                createChart(data.nodes, data.links);
            });
    });

    document.getElementById('btn-all').addEventListener('click', function() {
        createChart(allNodes, allLinks);
    });

    // Kullanıcı arama kısmı
    const userSearchInput = document.getElementById('user-search-input');
    const userSearchResults = document.getElementById('user-search-results');

    userSearchInput.addEventListener('keyup', function() {
        const query = userSearchInput.value;
        if (query.length > 1) {
            fetch(`/user-search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    userSearchResults.innerHTML = '';
                    if (data.results.length > 0) {
                        const ul = document.createElement('ul');
                        data.results.forEach(user => {
                            const li = document.createElement('li');
                            li.textContent = user.username;
                            li.addEventListener('click', function() {
                                fetch(`/map-data/?user_id=${user.id}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        createChart(data.nodes, data.links);
                                    });
                                userSearchResults.innerHTML = '';
                                userSearchInput.value = user.username;
                            });
                            ul.appendChild(li);
                        });
                        userSearchResults.appendChild(ul);
                    } else {
                        userSearchResults.innerHTML = '<p>Kullanıcı bulunamadı.</p>';
                    }
                });
        } else {
            userSearchResults.innerHTML = '';
        }
    });

    // Arama sonuçları dışında bir yere tıklanınca sonuçları gizle
    document.addEventListener('click', function(event) {
        if (!userSearchInput.contains(event.target)) {
            userSearchResults.innerHTML = '';
        }
    });
});
