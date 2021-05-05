'use strict';

class Canvas {
    canvas = document.querySelector('canvas');
    ctx = this.canvas.getContext('2d');

    zoom = 1.0;
    offsetX = 0.0;
    offsetY = 0.0;
    isMouseDown = false;

    widthFactor = 100;

    mouseX = 0;
    mouseY = 0;

    get screenWidth() { return this.canvas.width; }
    get screenHeight() { return this.canvas.height; }
    get width() { return this.convert({screenW: this.screenWidth}).w() }
    get height() { return this.convert({screenH: this.screenHeight}).h() }
    get leftmostX() { return -this.offsetX; }
    get rightmostX() { return this.leftmostX + this.width; }
    get topmostY() { return -this.offsetY; }
    get bottommostY() { return this.topmostY + this.height; }

    init() {
        $('#width-up').onclick = () => { this.widthFactor = R.clamp(0, 200, this.widthFactor + 10); }
        $('#width-down').onclick = () => { this.widthFactor = R.clamp(0, 200, this.widthFactor - 10); }

        this.canvas.onmousedown = () => { this.isMouseDown = true; }
        this.canvas.onmouseup = () => { this.isMouseDown = false; }

        this.canvas.onmousemove = (event) => {
            if (!this.isMouseDown) {
                const mouseScreenX = event.clientX - this.canvas.offsetLeft;
                const mouseScreenY = event.clientY - this.canvas.offsetTop;
                this.mouseX = this.convert({ screenX: mouseScreenX }).x();
                this.mouseY = this.convert({ screenY: mouseScreenY }).y();
                return;
            }

            const x = event.movementX / this.zoom;
            const y = event.movementY / this.zoom;
            this.ctx.translate(x, y);
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
            this.ctx.translate(-this.offsetX, -this.offsetY);
            this.ctx.scale(zoomFactor, zoomFactor);
            this.offsetX += mouseX / (this.zoom * zoomFactor) - mouseX / this.zoom;
            this.offsetY += mouseY / (this.zoom * zoomFactor) - mouseY / this.zoom;
            this.ctx.translate(this.offsetX, this.offsetY);
            this.zoom *= zoomFactor;
        }
    }

    timestampToX(date) { return this.secondsToW((date - new Date(2021, 4, 4)) / 1000) }
    XToTimestamp(x) { return new Date(+ new Date(2021, 4, 4) + this.WToSeconds(x) * 1000); }
    secondsToW(s) { return s / 3600 * this.widthFactor }
    WToSeconds(w) { return w * 3600 / this.widthFactor }

    convert({ screenX, screenY, screenW, screenH, x, y, w, h, ...rest }) {
        const result = {}
        if (Object.keys(rest).length > 0) throw new Error('Extra params are passed: ' + Object.keys(rest))
        if (screenX !== undefined) result.x = () => screenX / this.zoom - this.offsetX
        if (screenY !== undefined) result.y = () => screenY / this.zoom - this.offsetY
        if (x !== undefined) result.screenX = () => (x + this.offsetX) * this.zoom
        if (y !== undefined) result.screenY = () => (y + this.offsetY) * this.zoom
        if (screenW !== undefined) result.w = () => screenW / this.zoom
        if (screenH !== undefined) result.h = () => screenH / this.zoom
        if (w !== undefined) result.screenW = () => w * this.zoom
        if (h !== undefined) result.screenH = () => h * this.zoom
        if (Object.keys(result).length == 0) throw new Error('result is empty. Did you forget to pass a key?')
        return result
    }

    get currentPositionTime() {
        return this.XToTimestamp(this.mouseX);
    }

    renderBackground() {
        this.ctx.fillStyle = 'rgba(250, 250, 250)';
        this.ctx.fillRect( -this.offsetX, -this.offsetY, this.canvas.width / this.zoom, this.canvas.height / this.zoom);
    }

    renderTimeline() {
        const leftMostTime = this.XToTimestamp(this.leftmostX);
        const leftMostTimeRoundedDown = new Date(leftMostTime);
        leftMostTimeRoundedDown.setMinutes(0);
        leftMostTimeRoundedDown.setSeconds(0, 0);

        const x = this.timestampToX(new Date());
        this.ctx.beginPath();
        this.ctx.strokeStyle = 'red';
        this.ctx.moveTo(x, this.topmostY);
        this.ctx.lineTo(x, this.bottommostY);
        this.ctx.closePath();
        this.ctx.stroke();


        for (const h of R.range(0, 48)) {
            const tmpDate = new Date(leftMostTimeRoundedDown);
            tmpDate.setHours(tmpDate.getHours() + h);
            const x = this.timestampToX(tmpDate);
            this.ctx.beginPath();
            this.ctx.strokeStyle = 'black';
            this.ctx.moveTo(x, this.topmostY);
            this.ctx.lineTo(x, this.bottommostY);
            this.ctx.closePath();
            this.ctx.stroke();
        }
    }

    renderBoxes() {
        // globalThis.boxesXX.forEach(({ x, y, w, h, color, text }) => {
        //     x = x();
        //     w = w();
        //     this.context.fillStyle = color;
        //     this.context.fillRect(x, y, w, h);
        //     this.context.fillStyle = 'black';
        //     this.context.fillText(text, x, y, w * 2);
        // });
    }

    renderTooltip() {
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

    render() {
        $('#debug').innerHTML = ''
        this.renderBackground();
        this.renderTimeline();
        this.renderBoxes();
        this.renderTooltip();
        $('#width-value').innerHTML = this.widthFactor;
        $('#mouse-time').innerHTML = formatTime(this.currentPositionTime);
        $('#debug').innerHTML += `
                ${this.topmostY}
        ${this.leftmostX}                        ${this.rightmostX}

                ${this.bottommostY}
        `
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
// async function getNewBoxes() {
//     const x = await fetch('/data');
//     const inputTextText = await x.text();
//     const inputText = JSON.parse(inputTextText, dateReviver)
//     console.log(inputToBoxes(inputText));
//     return inputToBoxes(inputText);
// }

// getNewBoxes().then(x => globalThis.boxesXX = x)


const canv = new Canvas();
canv.init();
const interval = setInterval(() => canv.render(), 100)
let _errorCount = 0;

window.onerror = () => {
    _errorCount++;
    if (_errorCount > 10) {
        clearInterval(interval);
    }
}

