/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NameAndSignature } from "@web/core/signature/name_and_signature";
import { useState } from "@odoo/owl";


patch(NameAndSignature.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            signMode: "draw",
            showSignatureArea: !!(this.props.noInputName || this.defaultName),
            showFontList: false,
        });
    }
})
