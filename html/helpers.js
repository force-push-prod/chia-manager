'use strict';

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

function formatTime(d) {
    if (!(d instanceof Date)) throw new Error('Expect type Date, got ' + typeof(d))
    return formatTimeReadable(d) + '  ' + formatTimeRelative(d)
}

function formatTimeRelative(d) {
    const formatter = new Intl.RelativeTimeFormat(undefined, {
        numeric: "auto",
    })

    const DIVISIONS = [
        { amount: 60, name: "seconds" },
        { amount: 60, name: "minutes" },
        { amount: 24, name: "hours" },
        { amount: 7, name: "days" },
        { amount: 4.34524, name: "weeks" },
        { amount: 12, name: "months" },
        { amount: Number.POSITIVE_INFINITY, name: "years" },
    ]

    return formatTimeAgo(d)

    function formatTimeAgo(date) {
        let duration = (date - new Date()) / 1000

        for (let i = 0; i < DIVISIONS.length; i++) {
            const division = DIVISIONS[i]
            if (Math.abs(duration) < division.amount) {
                return formatter.format(Math.round(duration), division.name)
            }
            duration /= division.amount
        }
    }

}

function formatTimeReadable(date, withTimezone = false) {
    return (
        date.getFullYear() + '-' +
        TwoDigitPad(date.getMonth() + 1) + '-' +
        TwoDigitPad(date.getDate()) + ' ' +
        (
        date.getHours() === 0 && date.getMinutes() === 0 ? '' :
            TwoDigitPad(date.getHours()) + ':' +
            TwoDigitPad(date.getMinutes())) +
        (
        date.getSeconds() === 0 ? '' :
            (':' + TwoDigitPad(date.getSeconds()))
        ) +
        (
        !withTimezone ? '' :
            date.toString().substr(date.toString().indexOf('GMT'))
        )
    )

    function TwoDigitPad(s) {
        return s < 10 ? '0' + s : s;
    }
}
