import unittest

import artlist_scraper as app
import profiles


class ProfileModuleContractTests(unittest.TestCase):
    def test_all_builtin_profiles_are_importable_and_registered(self):
        module_names = [module.PROFILE_NAME for module in profiles.BUILTIN_MODULES]
        self.assertEqual(module_names, app.SiteProfile.all_names())
        for name, _contract, module in profiles.iter_contracts():
            self.assertTrue(callable(module.build), name)
            built = module.build(app.SiteProfile)
            self.assertEqual(built.name, name)

    def test_contract_catalog_and_item_urls_match_profiles(self):
        for name, contract, _module in profiles.iter_contracts():
            profile = app.SiteProfile.get(name)
            self.assertIsNotNone(profile, name)

            for url in contract.get("catalog_urls", []):
                normalized = profile.normalize_url(url)
                self.assertIsNotNone(normalized, (name, url))
                if profile.catalog_patterns:
                    self.assertTrue(profile.is_catalog(normalized), (name, url))

            for item in contract.get("item_urls", []):
                url = item["url"]
                normalized = profile.normalize_url(url)
                self.assertIsNotNone(normalized, (name, url))
                if profile.item_url_regex or profile.item_patterns:
                    self.assertTrue(profile.is_item(normalized), (name, url))
                expected = item.get("clip_id", "")
                if expected:
                    self.assertEqual(profile.extract_clip_id(normalized), expected, (name, url))

            for url in contract.get("excluded_urls", []):
                normalized = profile.normalize_url(url) or url
                self.assertTrue(profile.is_excluded(normalized), (name, url))

    def test_contract_video_urls_follow_profile_filters(self):
        for name, contract, _module in profiles.iter_contracts():
            profile = app.SiteProfile.get(name)
            for item in contract.get("video_urls", []):
                self.assertEqual(
                    profile.accepts_video_url(item["url"]),
                    item["allowed"],
                    (name, item["url"]),
                )


if __name__ == "__main__":
    unittest.main()
