# Title     : ggplots_pass_through
# Objective : Create publication-ready plots for pass-through paper using ggplot2
# Created by: Sebastian
# Created on: 02.06.2

library(tidyr)
library(ggplot2)
library(readxl)
library(RColorBrewer)

df_path <- 'D:/git_repos/medea/applications/pass_through'

# redefine scale
ggplot <- function(...) ggplot2::ggplot(...) +
    scale_color_brewer(palette = "Accent") +
    scale_fill_brewer(palette = "Accent")

# redefine theme
theme_set(theme_bw())

# -------------------------------------------------------------------------------------------
# FIGURE 2

df_base_Figure2 <- read_xlsx(file.path(df_path, 'ActGenByFuel_2017.xlsx'))
df_base_Figure2 <- df_base_Figure2[c(1, 2), 1 : 7]
names(df_base_Figure2) <- c("Source", "Nuclear", "Lignite", "Coal", "Gas", "Oil", "Biomass")

barz = c(
'#70B22F',
'#8249F4')

df_base_Figure2 %>%
    gather(Technology, Generation, - Source) %>%
    ggplot(aes(x = Technology, y = Generation)) +
    geom_bar(stat = "identity", aes(col = Source, fill = Source), position = position_dodge()) +
    scale_fill_manual(values = barz) +
    xlab("Generation Technology") +
    ylab("Generation [TWh/a]")
ggsave(file.path(df_path, 'Figure2_calibration.png'), width = 6.6, height = 3.7125, dpi = 600)

# -------------------------------------------------------------------------------------------
# data preparation

df_base <- read_xlsx(file.path(df_path, 'PsTru_Base_compile.xlsx'), sheet = 'price')
df_NImp075 <- read_xlsx(file.path(df_path, 'PsTru_in_NImp075_compile.xlsx'), sheet = 'price')
df_NImp125 <- read_xlsx(file.path(df_path, 'PsTru_in_NImp125_compile.xlsx'), sheet = 'price')
df_Coal075 <- read_xlsx(file.path(df_path, 'PsTru_in_Coal075_compile.xlsx'), sheet = 'price')
df_Coal125 <- read_xlsx(file.path(df_path, 'PsTru_in_Coal125_compile.xlsx'), sheet = 'price')
df_2025 <- read_xlsx(file.path(df_path, 'PsTru_RES2025_in_compile.xlsx'), sheet = 'price')
df_2030 <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_compile.xlsx'), sheet = 'price')
df_flex <- read_xlsx(file.path(df_path, 'PsTru_in_flex_compile.xlsx'), sheet = 'price')
df_2030_NImp075 <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_NImp075_compile.xlsx'), sheet = 'price')
df_2030_NImp125 <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_NImp125_compile.xlsx'), sheet = 'price')
df_2030_flex <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_flex50_compile.xlsx'), sheet = 'price')
df_2030_Coal075 <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_Coal075_compile.xlsx'), sheet = 'price')
df_2030_Coal125 <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_Coal125_compile.xlsx'), sheet = 'price')
df_2030_noCoal <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_noCoal_compile.xlsx'), sheet = 'price')
df_2030_noCoal_flex <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_noCoal_flex_compile.xlsx'), sheet = 'price')
df_2030_noLig <- read_xlsx(file.path(df_path, 'PsTru_RES2030_in_noLignite_compile.xlsx'), sheet = 'price')


# calc pass-through
rownames(df_base) <- df_base$level_0
df_base$level_0 <- NULL
rownames(df_NImp075) <- df_NImp075$level_0
df_NImp075$level_0 <- NULL
rownames(df_NImp125) <- df_NImp125$level_0
df_NImp125$level_0 <- NULL
rownames(df_Coal075) <- df_Coal075$level_0
df_Coal075$level_0 <- NULL
rownames(df_Coal125) <- df_Coal125$level_0
df_Coal125$level_0 <- NULL
rownames(df_2025) <- df_2025$level_0
df_2025$level_0 <- NULL
rownames(df_2030) <- df_2030$level_0
df_2030$level_0 <- NULL
rownames(df_flex) <- df_flex$level_0
df_flex$level_0 <- NULL
rownames(df_2030_NImp075) <- df_2030_NImp075$level_0
df_2030_NImp075$level_0 <- NULL
rownames(df_2030_NImp125) <- df_2030_NImp125$level_0
df_2030_NImp125$level_0 <- NULL
rownames(df_2030_flex) <- df_2030_flex$level_0
df_2030_flex$level_0 <- NULL
rownames(df_2030_Coal075) <- df_2030_Coal075$level_0
df_2030_Coal075$level_0 <- NULL
rownames(df_2030_Coal125) <- df_2030_Coal125$level_0
df_2030_Coal125$level_0 <- NULL
rownames(df_2030_noCoal) <- df_2030_noCoal$level_0
df_2030_noCoal$level_0 <- NULL
rownames(df_2030_noCoal_flex) <- df_2030_noCoal_flex$level_0
df_2030_noCoal_flex$level_0 <- NULL
rownames(df_2030_noLig) <- df_2030_noLig$level_0
df_2030_noLig$level_0 <- NULL


# current system
Central_Estimate <- diff(sapply(df_base, mean, na.rm = TRUE)) / 5
Low_Net_Imports <- diff(sapply(df_NImp075, mean, na.rm = TRUE)) / 5
High_Net_Imports <- diff(sapply(df_NImp125, mean, na.rm = TRUE)) / 5
Low_Coal_Price <- diff(sapply(df_Coal075, mean, na.rm = TRUE)) / 5
High_Coal_Price <- diff(sapply(df_Coal125, mean, na.rm = TRUE)) / 5
More_flexible <- diff(sapply(df_flex, mean, na.rm = TRUE)) / 5

CO2_Price <- seq(from = 0, to = 70, by = 5) + 5.71

# future system
Central_2025 <- diff(sapply(df_2025, mean, na.rm = TRUE)) / 5
Central_2030 <- diff(sapply(df_2030, mean, na.rm = TRUE)) / 5
Low_Net_Imports_2030 <- diff(sapply(df_2030_NImp075, mean, na.rm = TRUE)) / 5
High_Net_Imports_2030 <- diff(sapply(df_2030_NImp125, mean, na.rm = TRUE)) / 5
Low_Coal_Price_2030 <- diff(sapply(df_2030_Coal075, mean, na.rm = TRUE)) / 5
High_Coal_Price_2030 <- diff(sapply(df_2030_Coal125, mean, na.rm = TRUE)) / 5
More_flexible_2030 <- diff(sapply(df_2030_flex, mean, na.rm = TRUE)) / 5
No_Coal_2030 <- diff(sapply(df_2030_noCoal, mean, na.rm = TRUE)) / 5
No_Coal_flex_2030 <- diff(sapply(df_2030_noCoal_flex, mean, na.rm = TRUE)) / 5
No_Lignite_2030 <- diff(sapply(df_2030_noLig, mean, na.rm = TRUE)) / 5


pt_2017 <- data.frame(CO2_Price,
Central_Estimate,
Low_Net_Imports,
High_Net_Imports,
Low_Coal_Price,
High_Coal_Price,
More_flexible)

pt_2030 <- data.frame(CO2_Price,
                      Central_2025,
                      Central_2030,
                      Low_Net_Imports_2030,
                      High_Net_Imports_2030,
                      Low_Coal_Price_2030,
                      High_Coal_Price_2030,
                      More_flexible_2030,
                      No_Coal_2030, 
                      No_Coal_flex_2030,
                      No_Lignite_2030)

labz_replace <- data.frame(orig = c("Central_Estimate",
"High_Coal_Price",
"High_Net_Imports",
"Low_Coal_Price",
"Low_Net_Imports",
"More_flexible"),
repl = c('Base 2017',
'Coal price +25%',
'Net imports +25%',
'Coal price -25%',
'Net imports -25%',
'50% Ancillary Services'))

labz_replace_2030 <- data.frame(orig = c("Central_2025",
                                         "Central_2030",
                                         "Low_Net_Imports_2030",
                                         "High_Net_Imports_2030",
                                         "Low_Coal_Price_2030",
                                         "High_Coal_Price_2030",
                                         "More_flexible_2030",
                                         "No_Coal_2030", 
                                         "No_Coal_flex_2030",
                                         "No_Lignite_2030"),
                           repl = c('Base 2025',
                                    'Base_2030',
                                    'Net imports -25%',
                                    'Net imports +25%',
                                    'Coal price -25%',
                                    'Coal price +25%',
                                    '50% Ancillary Services',
                                    'No Coal plants',
                                    'No Coal plants & 50% Ancillary Services',
                                    'No Lignite plants'))


# transform data from 'wide'-format to 'long' format using dplyr
pt_long_2017 <- gather(pt_2017, scenario, passthrough, Central_Estimate : More_flexible)
pt_long_2030 <- gather(pt_2030, scenario, passthrough, Central_2025 : No_Lignite_2030)

#################FIGURE 3a - current system
ggplot(dplyr::filter(pt_long_2017, scenario %in% c("Central_Estimate")),
aes(x = CO2_Price, y = passthrough, colour = scenario, linetype = scenario, size = scenario)) +
    geom_line() +
    scale_color_manual(values = c("#000000"), labels = labz_replace) +
    scale_linetype_manual(values = c('solid', 'longdash', 'dotdash'), labels = labz_replace) +
    scale_size_manual(values = c(1.25, 0.75, 0.75), labels = labz_replace) +
    ylim(0.5, 1.0) +
    xlim(0, 80) +
xlab(bquote('Emission price [EUR per t'~CO[2]~']')) +
    ylab('Pass-through') +
    theme(legend.position = c(0.975, 0.975), legend.justification = c(1, 1)) +
    theme(legend.position = "none")
ggsave(file.path(df_path, 'Figure3a_ptru_base.png'), width = 6.6, height = 3.7125, dpi = 600)

#################FIGURE 3b - Future system
ggplot(dplyr::filter(pt_long_2030, scenario %in% c("Central_Estimate")),
       aes(x = CO2_Price, y = passthrough, colour = scenario, linetype = scenario, size = scenario)) +
  geom_line() +
  scale_color_manual(values = c("#000000"), labels = labz_replace_2030) +
  scale_linetype_manual(values = c('solid', 'longdash', 'dotdash'), labels = labz_replace_2030) +
  scale_size_manual(values = c(1.25, 0.75, 0.75), labels = labz_replace_2030) +
  #ylim(0.5, 1.0) +
  xlim(0, 80) +
  xlab(bquote('Emission price [EUR per t'~CO[2]~']')) +
  ylab('Pass-through') +
  theme(legend.position = c(0.975, 0.975), legend.justification = c(1, 1)) +
  theme(legend.position = "none")
ggsave(file.path(df_path, 'Figure3b_ptru_base.png'), width = 6.6, height = 3.7125, dpi = 600)

#################FIGURE 4A
fillz = c(
#'#30A0AD',
'#F7F31B',
'#474645',
'#7F4A08',
'#3AAD30',
'#AD2506')

df_fuel <- read_xlsx(file.path(df_path, 'PsTru_ic_Base_compile.xlsx'), sheet = 'annual_fuelburn')
df_fuel <- df_fuel[1 : 16, 2 : 7]
df_fuel <- df_fuel %>%
    sapply(as.character) %>%
    tibble::as_tibble() %>%
    sapply(as.double) %>%
    tibble::as_tibble()

#

df_fuel_ <- (df_fuel / 1000) %>%
    tibble::as_tibble() %>%
    dplyr::mutate(CO2_Price = (seq(from = 0, to = 75, by = 5) + 5.71))

fuel_long <- gather(df_fuel_, fuel, TWh, Nuclear : Biomass)


fuel_long$fuel <- factor(fuel_long$fuel, levels = rev(c("Nuclear", "Biomass", "Lignite", "Coal", "Gas", "Oil")))

ggplot(fuel_long, aes(x = CO2_Price, y = TWh, fill = fuel)) +
  geom_area() + 
  scale_fill_manual(values = fillz) +
    ylab(bquote('Fuel burn [TWh]')) +
xlab(bquote('Emission price [EUR per t'~CO[2]~']'))
ggsave(file.path(df_path, 'Figure4a_fuel_burn.png'), width = 4.422, height = 3.7125, dpi = 600, units = 'in')

#################FIGURE 4B - Emissions
em_factors <- tibble::tibble(fuel = c("Nuclear", "Lignite", "Coal", "Gas", "Oil", "Biomass"),
em_facts = c(0, 0.45, 0.33, 0.199, 0.275, 0))

fuel_long_emissions <- dplyr::full_join(fuel_long, em_factors) %>% dplyr::mutate(Emissions = TWh * em_facts)

fuel_long_emissions$fuel <- factor(fuel_long$fuel, levels = rev(c("Nuclear", "Biomass", "Lignite", "Coal", "Gas", "Oil")))

ggplot(fuel_long_emissions, aes(x = CO2_Price, y = Emissions, fill = fuel)) +
    geom_area() +
    scale_fill_manual(values = fillz) +
ylab(bquote('Emissions [Mn t'~CO[2]~']')) +
xlab(bquote('Emission price [EUR per t'~CO[2]~']'))
ggsave(file.path(df_path, 'Figure4b_emissions.png'), width = 4.422, height = 3.7125, dpi = 600, units = 'in')




#################FIGURE 5

# generate plot using subset of data
colz <- c(
'#53D8FB',
'#191919',
'#B1B9C6',
'#8C939E',
'#8249F4',
'#4250F4',
'#4CD398',
'#1aBF98')
#          '#FFFFFF')

#'#30786B', 
#'#298C26', 
#'#70B22F', 
#'#B8D939', 
#'#FFFF42', 
#'#FFFFA0', 


####str_replace_all is a vectorized version without loops
####but needs named elements which suck
pt_long_2017 <- pt_long_2017 %>% dplyr::mutate(Scenario = scenario)
for (i in 1 : nrow(labz_replace)) {
    pt_long_2017 <- pt_long_2017 %>% dplyr::mutate(Scenario = gsub(labz_replace[i, 1], labz_replace[i, 2], Scenario))
}

pt_long_2017 %>%
ggplot(aes(x = CO2_Price, y = passthrough, colour = Scenario, linetype = Scenario, size = Scenario)) +
    geom_line() +
    scale_color_manual(values = colz) +
    scale_linetype_manual(values = c('longdash', 'solid', 'longdash', 'dotdash', 'longdash', 'dotdash', 'longdash', 'dotdash')) +
    scale_size_manual(values = c(1.25, 2.0, 1.25, 1.25, 1.25, 1.25, 1.25, 1.25)) +
    ylim(0.25, 1.0) +
    xlim(0, 80) +
xlab(bquote('Emission price [EUR per t'~CO[2]~']')) +
    ylab('Pass-through')
ggsave(file.path(df_path, 'Figure5_sensitivity.png'), width = 6.6, height = 3.7125, dpi = 600)


