"""Native national-spirit artwork. Pure authoring helper; writes no files.

Every picture key below is a GFX_idea_<key> sprite in the installed ideas.gfx.
These sprites reference installed DDS assets; no third-party art is copied.
"""
PICTURE_GROUPS={
 'generic_flexible_foreign_policy':'kaz_initial usa_oceans',
 'generic_local_self_management':'kaz_local_compacts sov_local bra_federal_settlement',
 'generic_exploit_mines':'kaz_resource_gap',
 'generic_agrarian_reform':'kaz_land_settlement mex_initial chi_land_settlement',
 'generic_central_management':'kaz_mandate_settlement cau_central_settlement sib_directory_settlement sov_initial sov_central cmt_board_settlement bra_officers_settlement usa_business',
 'generic_license_production':'kaz_standards',
 'generic_infantry_bonus':'kaz_maintained_army jap_logistics usa_repair territorial',
 'generic_disjointed_gov':'cau_initial bra_initial chi_initial',
 'generic_fortify_the_borders':'cau_neutral naf_neutral armed_neutrality',
 'generic_build_infrastructure':'sib_initial',
 'generic_pp_unity_bonus':'sib_russia_settlement civil_service',
 'generic_goods_red_bonus':'sov_recovery_settlement arg_initial usa_welfare',
 'generic_flexible_foreign_policy2':'sov_treaty_settlement arg_league_settlement jap_inquiry',
 'generic_communist_army':'sov_pressure_settlement',
 'generic_victors_of_ww1':'naf_initial',
 'generic_foreign_capital':'cmt_initial cmt_patrons_settlement usa_contracts usa_credit jap_obligations concession export_orders',
 'generic_production_bonus':'mex_oil_settlement arg_industry_settlement usa_profit workshop_network',
 'generic_reserve_divisions':'mex_officers_settlement chi_army_settlement jap_commands jap_garrison jap_land',
 'generic_sea_focused_navy':'arg_atlantic_settlement jap_sea commandsea',
 'generic_research_bonus':'usa_universities usa_project jap_labs jap_engineers applied_institute',
 'generic_morale_bonus':'usa_labor',
 'generic_constitutional_guarantees':'kaz_constitution_settlement cau_compact_settlement sib_civil_settlement naf_citizen cmt_residents_settlement mex_law_settlement bra_republic_settlement chi_agreement_settlement jap_treaty usa_antitrust',
 'generic_war_preparation':'usa_tutelage jap_pressure',
 'generic_armor':'usa_tanks mobile breakthrough',
 'generic_coastal_navy':'usa_convoys jap_shipping safepassage',
 'generic_volunteer_expedition_bonus':'expedition',
 'generic_air_bonus':'frontsky',
 'generic_air_research':'interdiction',
 'generic_navy_bonus':'seasky',
 'generic_coastal_defense_ships2':'denysea',
}
PICTURES={key:picture for picture,keys in PICTURE_GROUPS.items() for key in keys.split()}
def idea_picture(ident):
    """Return the native picture suffix expected by a country idea definition."""
    return PICTURES.get(ident.removeprefix('aof_v03_'),'generic_production_bonus')
