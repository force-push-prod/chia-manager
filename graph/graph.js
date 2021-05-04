function $(selector, base = null) {
    base = (base === null) ? document : base;
    return base.querySelector(selector);
}

function $$(selector, base = null) {
    base = (base === null) ? document : base;
    return Array.from(base.querySelectorAll(selector));
}


const canvas = document.querySelector('canvas');
const context = canvas.getContext('2d');

let zoom = 1.0;
let offsetX = 0.0;
let offsetY = 0.0;
let isMouseDown = false;

let widthFactor = 100;

let currentMousePosition = [0, 0];

const INPUT = '[{"stages_start_time": {"1": "2021-05-03T01:43:19", "2": "2021-05-03T05:07:58", "3": "2021-05-03T06:32:39", "4": "2021-05-03T09:46:00"}, "stages_took_seconds": {"1": 12279.437, "2": 5081.001, "3": 11600.859, "4": 901.438}, "total_time_seconds": 29862.737, "current_bucket": 126, "current_table": 6, "error": ""}, {"stages_start_time": {"1": "2021-05-03T10:01:04", "2": "2021-05-03T13:37:26", "3": "2021-05-03T15:14:58", "4": "2021-05-03T18:35:56"}, "stages_took_seconds": {"1": 12981.79, "2": 5851.366, "3": 12057.474, "4": 791.013}, "total_time_seconds": 31681.647, "current_bucket": 126, "current_table": 6, "error": ""}, {"stages_start_time": {"1": "2021-05-03T20:25:48", "2": "2021-05-03T23:58:07"}, "stages_took_seconds": {"1": 12738.844}, "total_time_seconds": 0.0, "current_bucket": 1, "current_table": 5, "error": ""}]'
function dateReviver(k, v) {
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*(([-+]\d{4})|Z)$/.test(v)) return new Date(v);
    // HACK: If there is no timezone, default to EDT
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(v)) return new Date(v + '-0400');
    else return v;
}
const INPUT_PARSED = JSON.parse(INPUT, dateReviver)
console.log(INPUT_PARSED);
let boxes = inputToBoxes(INPUT_PARSED);


function timestampToX(date) {
    // console.log(secondsToWidth(date - new Date(2021, 4, 1)));
    return secondsToWidth((date - new Date(2021, 4, 4)) / 1000)
}

function secondsToWidth(seconds) {
    return seconds / 3600 * widthFactor
}

function inputToBoxes(input) {
    const boxes = [];
    input.forEach((plot, index) => {
        for (let stageId of [1,2,3,4]) {
            if (!(stageId in plot['stages_start_time']))
                continue

            const startTimestamp = plot['stages_start_time'][stageId]
            const tookSeconds = plot['stages_took_seconds'][stageId] || ((new Date() - plot['stages_start_time']) / 1000)
            boxes.push({
                x: () => timestampToX(startTimestamp),
                y: 80 * index,
                w: () => secondsToWidth(tookSeconds),
                h: 50,
                text: `${index} - ${stageId}`,
                tooltip: `${startTimestamp}`,
                color: `hsla(${stageId * 20}, 50%, 50%, 0.3)`,
            })
        }
    })

    return boxes
}

function drawBackground() {
    context.fillStyle = 'rgba(250, 250, 250)';
    context.fillRect(
        -offsetX,
        -offsetY,
        canvas.width / zoom,
        canvas.height / zoom
    );
}

function drawBoxes() {
    boxes.forEach(({ x, y, w, h, color, text }) => {
        x = x();
        w = w();
        context.fillStyle = color;
        context.fillRect(x, y, w, h);
        context.fillStyle = 'black';
        context.fillText(text, x, y, w * 2);
    });
}

function render() {
    drawBackground();
    drawBoxes();
    drawTooltip(currentMousePosition);
    $('#width-value').innerHTML = widthFactor;

}

function drawTooltip([clientX, clientY]) {
    const mouseX = clientX - canvas.offsetLeft;
    const mouseY = clientY - canvas.offsetTop;
    // TODO: Massive optimization. Compute mouseX and mouseY instead of converting all boxes
    const coordinatesRelativeToScreen = boxes.map(({x, y, w, h, ...rest}) => ({
        x: (x() + offsetX) * zoom,
        y: (y + offsetY) * zoom,
        w: w() * zoom,
        h: h * zoom,
        ...rest,
    }));

    coordinatesRelativeToScreen.forEach(({x, y, w, h, tooltip = '...'}) => {
        const withinX = x < mouseX && mouseX < x + w;
        const withinY = y < mouseY && mouseY < y + h;

        if (withinX && withinY) {
            context.fillStyle = 'black'
            context.fillText(tooltip, (x / zoom - offsetX), (y / zoom - offsetY) + 20)
      }
    });
}


// HANDLERS - buttons
$('#width-up').onclick = () => { widthFactor = R.clamp(0, 200, widthFactor + 10); }
$('#width-down').onclick = () => { widthFactor = R.clamp(0, 200, widthFactor - 10); }




// HANDLERS - canvas

canvas.onwheel = (event) => {
    // Adapted from https://stackoverflow.com/a/3151987
    event.preventDefault();
    const mouseX = event.clientX - canvas.offsetLeft;
    const mouseY = event.clientY - canvas.offsetTop;
    const wheel = Math.sign(-event.deltaY);
    const zoomFactor = Math.exp(wheel * 0.1);
    context.translate(-offsetX, -offsetY);
    context.scale(zoomFactor, zoomFactor);
    offsetX += mouseX / (zoom * zoomFactor) - mouseX / zoom;
    offsetY += mouseY / (zoom * zoomFactor) - mouseY / zoom;
    context.translate(offsetX, offsetY);
    zoom *= zoomFactor;
}


canvas.onmousedown = () => { isMouseDown = true; }
canvas.onmouseup = () => { isMouseDown = false; }



canvas.onmousemove = (event) => {
    if (!isMouseDown) {
        // console.count();
        currentMousePosition = [event.clientX, event.clientY];
        return;
    }

    const x = event.movementX / zoom;
    const y = event.movementY / zoom;
    context.translate(x, y);
    offsetX += x;
    offsetY += y;
}

const interval = setInterval(render, 100)
let _errorCount = 0;
window.onerror = () => {
    _errorCount++;
    if (_errorCount > 10)
        clearInterval(interval)
}

