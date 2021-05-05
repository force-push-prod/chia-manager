function $(selector, base = null) {
    base = (base === null) ? document : base;
    return base.querySelector(selector);
}

function $$(selector, base = null) {
    base = (base === null) ? document : base;
    return Array.from(base.querySelectorAll(selector));
}

function dateReviver(k, v) {
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*(([-+]\d{4})|Z)$/.test(v)) return new Date(v);
    // HACK: If there is no timezone, default to EDT
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(v)) return new Date(v + '-0400');
    else return v;
}


class Canvas {
    canvas = document.querySelector('canvas');
    context = canvas.getContext('2d');

    zoom = 1.0;
    offsetX = 0.0;
    offsetY = 0.0;
    isMouseDown = false;

    widthFactor = 100;

    currentMousePosition = [0, 0];

    init() {
        $('#width-up').onclick = () => { this.widthFactor = R.clamp(0, 200, this.widthFactor + 10); }
        $('#width-down').onclick = () => { this.widthFactor = R.clamp(0, 200, this.widthFactor - 10); }

        this.canvas.onmousedown = () => { this.isMouseDown = true; }
        this.canvas.onmouseup = () => { this.isMouseDown = false; }

        this.canvas.onmousemove = (event) => {
            if (!this.isMouseDown) {
                this.currentMousePosition = [event.clientX, event.clientY];
                return;
            }

            const x = event.movementX / this.zoom;
            const y = event.movementY / this.zoom;
            this.context.translate(x, y);
            this.offsetX += x;
            this.offsetY += y;
        }

        this.canvas.onwheel = (event) => {
            // Adapted from https://stackoverflow.com/a/3151987
            event.preventDefault();
            const mouseX = event.clientX - this.canvas.offsetLeft;
            const mouseY = event.clientY - this.canvas.offsetTop;
            const wheel = Math.sign(-event.deltaY);
            const zoomFactor = Math.exp(wheel * 0.1);
            this.context.translate(-this.offsetX, -this.offsetY);
            this.context.scale(zoomFactor, zoomFactor);
            this.offsetX += mouseX / (this.zoom * zoomFactor) - mouseX / this.zoom;
            this.offsetY += mouseY / (this.zoom * zoomFactor) - mouseY / this.zoom;
            this.context.translate(this.offsetX, this.offsetY);
            this.zoom *= zoomFactor;
        }
    }

    timestampToX(date) {
        return secondsToWidth((date - new Date(2021, 4, 4)) / 1000)
    }

    secondsToWidth(seconds) {
        return seconds / 3600 * this.widthFactor
    }

    convert({ screenX, screenY, screenW, screenH, x, y, w, h }) {
        const result = {}
        if (screenX)
            result.x = screenX / this.zoom - this.offsetX
        if (screenY)
            result.y = screenY / this.zoom - this.offsetY
        if (x)
            result.screenX = (x + this.offsetX) * this.zoom
        if (y)
            result.screenY = (y + this.offsetY) * this.zoom
        if (screenW)
            result.w = screenW / this.zoom
        if (screenH)
            result.h = screenH / this.zoom
        if (w)
            result.screenW = w * this.zoom
        if (h)
            result.screenH = h * this.zoom
    }

    renderBackground() {
        this.context.fillStyle = 'rgba(250, 250, 250)';
        this.context.fillRect(
            -this.offsetX,
            -this.offsetY,
            this.canvas.width / this.zoom,
            this.canvas.height / this.zoom
            );

            this.context.fillStyle = 'black';
            this.context.fillRect(10, 20, 30, 40)
    }

    renderTooltip() {
        const [clientX, clientY] = this.currentMousePosition;
        const mouseX = clientX - this.canvas.offsetLeft;
        const mouseY = clientY - this.canvas.offsetTop;
        // TODO: Massive optimization. Compute mouseX and mouseY instead of converting all boxes
        // const coordinatesRelativeToScreen = globalThis.boxesXX.map(({x, y, w, h, ...rest}) => ({
        //     x: (x() + this.offsetX) * this.zoom,
        //     y: (y + this.offsetY) * this.zoom,
        //     w: w() * this.zoom,
        //     h: h * this.zoom,
        //     ...rest,
        // }));

        // coordinatesRelativeToScreen.forEach(({x, y, w, h, tooltip = '...'}) => {
        //     const withinX = x < mouseX && mouseX < x + w;
        //     const withinY = y < mouseY && mouseY < y + h;

        //     if (withinX && withinY) {
        //         this.context.fillStyle = 'black'
        //         this.context.fillText(tooltip, (x / this.zoom - this.offsetX), (y / this.zoom - this.offsetY) + 20)
        //   }
        // });
    }

    renderBoxes() {
        globalThis.boxesXX.forEach(({ x, y, w, h, color, text }) => {
            x = x();
            w = w();
            this.context.fillStyle = color;
            this.context.fillRect(x, y, w, h);
            this.context.fillStyle = 'black';
            this.context.fillText(text, x, y, w * 2);
        });
    }

    render() {
        this.renderBackground();
        this.renderBoxes();
        this.renderTooltip();
        $('#width-value').innerHTML = this.widthFactor;
    }
}


function inputToBoxes(input) {
    const boxes = [];
    input.forEach((plot, index) => {
        for (let stageId of [1, 2, 3, 4]) {
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

globalThis.boxesXX = [];
async function getNewBoxes() {
    const x = await fetch('/data');
    const inputTextText = await x.text();
    const inputText = JSON.parse(inputTextText, dateReviver)
    console.log(inputToBoxes(inputText));
    return inputToBoxes(inputText);
}

getNewBoxes().then(x => globalThis.boxesXX = x)


const canv = new Canvas();
canv.init();
const interval = setInterval(() => canv.render(), 100)
let _errorCount = 0;
window.onerror = () => {
    _errorCount++;
    if (_errorCount > 10)
        clearInterval(interval)
}

