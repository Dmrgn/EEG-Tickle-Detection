<template>
    <div ref="containerElm" class="relative">
        <img hidden ref="brainImgOutline" width="400px" height="488px" class="relative z-10" src="../assets/brain_outline.png" alt="brain">
        <img @load="onLoad" ref="brainImg" width="400px" height="488px" class="relative z-10" src="../assets/brain.png" alt="brain">
        <div class="absolute top-0 left-0 z-20">
            <div id="heatmap" class="bg-[#2B2D31] w-[400px] h-[488px]"></div>
        </div>
        <canvas @click="onClick" ref="can" class="absolute top-0 left-0 z-30"></canvas>
        <button class="absolute bottom-[-1px] left-0 z-40 bg-[#2B2D31] hover:bg-[#1B1D21] transition-colors p-2" @click="showDebugText = !showDebugText">{{showDebugText ? 'Hide' : 'Show'}} Debug</button>
    </div>
</template>

<script setup>
import h337 from 'heatmap.js';
import {onMounted, ref, watch} from 'vue';

import eegPos from '../assets/eeg_pos.json'

const {eegData, frameNumber} = defineProps({
    eegData: Object,
    frameNumber: Number
})

const electrodeSelected = defineModel();

const containerElm = ref(null);
const brainImg = ref(null);
const brainImgOutline = ref(null);
const can = ref(null);
const brainImgWidth = ref(0);
const brainImgHeight = ref(0);
const showDebugText = ref(false);
let heatmap = null;
let click_pos = [];
let ctx = null;

watch(()=>frameNumber, () => {
    updateHeatMap(frameNumber);
    drawBrainDiagram();
})

watch(showDebugText, () => {
    drawBrainDiagram();
})

function updateHeatMap(frameNumber) {
    heatmap.setData({
        max: 80,
        min: -20,
        data: eegData[frameNumber].map((value, i)=>{
            return {
                x: eegPos[i].x*brainImgWidth.value,
                y: eegPos[i].y*brainImgHeight.value,
                value: value,
            }
        })
    })
}
function drawBrainDiagram() {
    ctx = can.value.getContext('2d');
    can.value.width = brainImgWidth.value;
    can.value.height = brainImgHeight.value;
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, brainImgWidth.value, brainImgHeight.value);
    ctx.drawImage(brainImg.value, 0, 0, brainImgWidth.value, brainImgHeight.value);
    ctx.globalCompositeOperation = 'multiply';
    ctx.drawImage(heatmap._renderer.canvas, 0, 0, brainImgWidth.value, brainImgHeight.value);
    ctx.globalCompositeOperation = 'source-over';
    ctx.drawImage(brainImgOutline.value, 0, 0, brainImgWidth.value, brainImgHeight.value);
    if (showDebugText.value) {
        for (let i = 0; i < eegData[frameNumber].length; i++) {
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.ellipse(eegPos[i].x*brainImgWidth.value, eegPos[i].y*brainImgHeight.value-20, 8, 8, 0, 0, 2*Math.PI);
            ctx.fill();
            ctx.fillStyle = 'black';
            ctx.beginPath();
            ctx.ellipse(eegPos[i].x*brainImgWidth.value, eegPos[i].y*brainImgHeight.value-20, 5, 5, 0, 0, 2*Math.PI);
            ctx.fill();
            ctx.fillRect(eegPos[i].x*brainImgWidth.value-10, eegPos[i].y*brainImgHeight.value-40, 20, 10);
            if (electrodeSelected.value == i) {
                ctx.fillStyle = 'red';
            } else {
                ctx.fillStyle = 'white';
            }
            ctx.fillText(Math.round(eegData[frameNumber][i]*10, 2)/10, eegPos[i].x*brainImgWidth.value-10, eegPos[i].y*brainImgHeight.value-30);
        }
    }
}

function onLoad() {
    drawBrainDiagram();
}
onMounted(async () => {
    window.h337 = h337
    brainImgWidth.value = brainImg.value.width;
    brainImgHeight.value = brainImg.value.height;

    containerElm.value.addEventListener('click', (event) => {
        click_pos = [event.offsetX, event.offsetY];
        let closest = -1;
        let min_dist = Number.MAX_SAFE_INTEGER;
        for (let i = 0; i < eegPos.length; i++) {
            if (Math.sqrt(Math.pow(eegPos[i].x*brainImgWidth.value - click_pos[0], 2) + Math.pow(eegPos[i].y*brainImgHeight.value - click_pos[1], 2)) < min_dist) {
                min_dist = Math.sqrt(Math.pow(eegPos[i].x*brainImgWidth.value - click_pos[0], 2) + Math.pow(eegPos[i].y*brainImgHeight.value - click_pos[1], 2));
                closest = i;
            }
        }
        if (closest !== -1) {
            electrodeSelected.value = closest;
        }
    })

    heatmap = h337.create({
        container: document.getElementById('heatmap'),
        radius: 65,
        maxOpacity: 1,
        minOpacity: 0.5,
        blur: .4,
        gradient: {
            // enter n keys between 0 and 1 here
            // for gradient color customization
            '0': 'blue',
            '0.25': 'white',
            '1': 'red'
        }
    });
    updateHeatMap(frameNumber);
})
</script>

<style scoped>
</style>
