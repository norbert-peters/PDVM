import React, { useState } from "react"
import { Link as RouterLink } from 'react-router-dom'
import Tooltip from '@material-ui/core/Tooltip';
import IconButton from '@material-ui/core/IconButton'


export const PdvmIconButton = (props) => {
    const [ttitle] = useState(props.ttitle)
    const [togo] = useState(props.togo)
    const [nicon] = useState(props.nicon)

    return (
        <Tooltip title={ttitle} interactive>
            <IconButton
                color="inherit"
                edge="end"
                component={RouterLink}
                to={togo}
            >
            {nicon}
            </IconButton>                 
        </Tooltip>
    )
}