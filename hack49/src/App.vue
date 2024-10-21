<template>
    <div class="flex items-center justify-center">
        <div class="flex items-center">
            <button class="bg-[#2B2D31] p-4 hover:hover:bg-[#1B1D21] transition-colors" @click="frameNumber++">Next
                Frame</button>
            <button class="bg-[#2B2D31] p-4 border-l-gray-600 border-l-2 hover:hover:bg-[#1B1D21] transition-colors"
                @click="isPlaying ? pause() : play()">{{ isPlaying ? '⏸️' : '▶️' }}</button>
            <h2 class="ml-4 ">Frame:</h2>
            <h2 class="w-[50px] text-right">{{ frameNumber }}</h2>
            <h2>/{{ s04_rest_close.length - 1 }}</h2>
            <input class="w-[500px] ml-4 " type="range" min="0" :max="s04_rest_close.length - 1" step="1"
                v-model="frameNumber">
            <button class="bg-[#2B2D31] p-4 ml-4 hover:hover:bg-[#1B1D21] transition-colors" @click="frameNumber = 0">↩️</button>
            <h2 class="ml-4 ">Frame Rate:</h2>
            <h2 class="w-[50px] text-right">{{ frameRate }}fps</h2>
            <input class="w-[100px] ml-4" type="range" min="10" max="510" step="10" v-model="frameRate">
        </div>
    </div>
    <div class="xl:flex items-center justify-center mt-8">
        <Brain :eegData="s04_rest_open" :frameNumber="Number(frameNumber)" v-model="electrodeSelected" />
        <Spectro v-model="predictions" :eegData="s04_rest_open.map((x) => { return x[electrodeSelected] })" :frameNumber="Number(frameNumber)" />
    </div>
    <div class="flex w-full justify-center">
        <div class="p-6 bg-[#2B2D31] w-[1200px] mt-8">
            <div class="space-y-6 max-w-md mx-auto">
                <h1 class="text-3xl font-bold mb-6 text-left">Patient State Prediction</h1>
                <div v-for="(index) in [1, 0, 2]" :key="index">
                    <div class="flex justify-between mb-1">
                        <span class="text-lg font-semibold text-[#81838D]" :class="Math.max(...predictions) === predictions[index] ? 'font-bold text-white' : ''">{{ predictionLabels[index] }}</span>
                        <span class="text-lg font-semibold text-[#81838D]" :class="Math.max(...predictions) === predictions[index] ? 'font-bold text-white' : ''">{{ (predictions[index] * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="w-full bg-[#81838D] rounded-full h-6" :class="Math.max(...predictions) === predictions[index] ? 'font-bold bg-white' : ''">
                        <div class="h-6 rounded-full" :class="progressBarClass(index)"
                            :style="{ width: (predictions[index] * 100) + '%' }"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import h337 from 'heatmap.js';
import { onMounted, ref, nextTick, watch } from 'vue';
import Brain from './components/Brain.vue'
import Spectro from './components/Spectro.vue'

import s04_rest_close from './assets/data/s04_rest_close.json'
import s04_rest_open from './assets/data/s04_rest_open.json'

const frameNumber = ref(0);
const frameRate = ref(30);
const isPlaying = ref(false);
const playInterval = ref(null);
const electrodeSelected = ref(0);
const catElm = ref(null);
const predictions = ref([0, 0, 0]);
const predictionLabels = ['Anesthesia', 'No Anesthesia or Tickling', 'Anesthesia & Tickling'];
function progressBarClass(index) {
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-red-500'];
    return `${colors[index]} transition-all duration-500`;
}

watch(frameRate, () => {
    if (isPlaying.value) {
        clearInterval(playInterval.value);
        play();
    }
})

function play() {
    isPlaying.value = true;
    frameNumber.value = Number(frameNumber.value);
    playInterval.value = setInterval(() => {
        frameNumber.value += frameRate.value < 100 ? 1 : (frameRate.value < 300 ? 8 : 16);
        if (frameNumber.value >= s04_rest_open.length - 1) {
            frameNumber.value = 0;
        }
    }, (frameRate.value < 100 ? 1000 / frameRate.value : (frameRate.value < 300 ? 1000 / (frameRate.value / 8) : 1000 / (frameRate.value / 16))));
}

function pause() {
    isPlaying.value = false;
    clearInterval(playInterval.value);
}

document.addEventListener("keydown", function (e) {
    if (e.key === " ") {
        if (isPlaying.value) pause();
        else play();
    } else if (e.key === "ArrowRight") {
        frameNumber.value++;
        if (frameNumber.value >= s04_rest_open.length - 1) {
            frameNumber.value = 0;
        }
    } else if (e.key === "ArrowLeft") {
        frameNumber.value--;
        if (frameNumber.value < 0) {
            frameNumber.value = s04_rest_open.length - 1;
        }
    } else if (e.key === "ArrowUp") {
        frameRate.value += 10;
    } else if (e.key === "ArrowDown") {
        frameRate.value -= 10;
    } else if (e.key === "t") {
        electrodeSelected.value++;
        if (electrodeSelected.value > 31) {
            electrodeSelected.value = 0;
        }
    }
})

onMounted(async () => {
    window.h337 = h337;
})
</script>

<style scoped></style>
