/*
  watchdog.c - independent watchdog (IWDG) against a frozen CPU

  The IWDG runs on its own clock (LSI). It is refreshed in the SysTick interrupt, every millisecond,
  so it only fires when the CPU core stops: then the controller restarts after about 2 s with all
  outputs off (laser, spindle) instead of standing still with them on.

  Seen 2026-11 on the Octopus Pro: during SD card uploads the core locked up now and then (no
  interrupt ran any more, no fault handler), more often with WiFi active nearby.

  $I shows the cause of the last reset and how many watchdog resets happened since power on
  (kept in the backup SRAM, which survives a reset but not a power cycle).
*/

#include "driver.h"

#if WATCHDOG_ENABLE

#include <stdio.h>

#include "grbl/hal.h"
#include "grbl/report.h"

#define WDG_MAGIC 0x57444F47    // "WDOG"

typedef struct {
    uint32_t magic;
    uint32_t resets;            // watchdog resets since power on
} wdg_store_t;

#define store ((volatile wdg_store_t *)BKPSRAM_BASE)

static uint32_t reset_flags;
static on_report_options_ptr on_report_options;

static void report_options (bool newopt)
{
    char buf[100];

    on_report_options(newopt);

    if(newopt)
        return;

    report_plugin("Watchdog", "1.00");

    snprintf(buf, sizeof(buf), "[WATCHDOG:last reset by%s%s%s%s%s, watchdog resets since power on %lu]" ASCII_EOL,
              reset_flags & RCC_CSR_IWDGRSTF ? " WATCHDOG" : "", reset_flags & RCC_CSR_BORRSTF ? " BROWNOUT" : "",
              reset_flags & RCC_CSR_PORRSTF ? " POWER" : "", reset_flags & RCC_CSR_PINRSTF ? " PIN" : "",
              reset_flags & RCC_CSR_SFTRSTF ? " SOFTWARE" : "", (unsigned long)store->resets);
    hal.stream.write(buf);
}

void watchdog_init (void)
{
    RCC->APB1ENR |= RCC_APB1ENR_PWREN;
    __DSB();
    PWR->CR |= PWR_CR_DBP;
    RCC->AHB1ENR |= RCC_AHB1ENR_BKPSRAMEN;
    __DSB();

    reset_flags = RCC->CSR;
    RCC->CSR |= RCC_CSR_RMVF;

    if(store->magic != WDG_MAGIC || (reset_flags & (RCC_CSR_PORRSTF | RCC_CSR_BORRSTF))) {
        store->magic = WDG_MAGIC;
        store->resets = 0;
    }
    if(reset_flags & RCC_CSR_IWDGRSTF)
        store->resets++;

    // LSI about 32 kHz / 64 = 500 Hz, reload 1000: 2 s; refreshed in SysTick_Handler (stm32f4xx_it.c)
    IWDG->KR = 0x5555;
    IWDG->PR = 4;
    IWDG->RLR = 1000;
    IWDG->KR = 0xAAAA;
    IWDG->KR = 0xCCCC;

    on_report_options = grbl.on_report_options;
    grbl.on_report_options = report_options;
}

#endif // WATCHDOG_ENABLE
